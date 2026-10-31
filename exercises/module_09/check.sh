#!/usr/bin/env bash
# Checks the module 9 exercise on the current branch.
#
#   claude -p "Utilise le sous-agent test-reviewer sur tests/test_unpaid_report.py." \
#       --output-format stream-json --verbose < /dev/null > review.jsonl
#   bash <(git show origin/course:exercises/module_09/check.sh) review.jsonl
#
# Run it from the root of the project, on your exercise-09 branch. It reads the
# subagent file and the stream-json output of the run; it does not call claude.
set -u
AGENT=.claude/agents/test-reviewer.md
STREAM=${1:-}
failed=0

ok()   { printf 'OK    %s\n' "$1"; }
fail() { printf 'FAIL  %s\n' "$1"; failed=$((failed + 1)); }

if [ -z "$STREAM" ] || [ ! -s "$STREAM" ]; then
    echo "usage: bash check.sh <stream-json file of the run>" >&2; exit 2
fi
if ! git rev-parse -q --verify exercise-09-start >/dev/null; then
    echo "The tag exercise-09-start is missing: see the README of the exercise." >&2; exit 2
fi

# 1. The subagent file and its frontmatter.
if [ -f "$AGENT" ]; then ok "$AGENT exists"; else fail "$AGENT exists"; fi
front=$(awk 'NR==1 && $0!="---"{exit} NR>1 && $0=="---"{exit} NR>1{print}' "$AGENT" 2>/dev/null)
if printf '%s\n' "$front" | grep -qE '^name:[[:space:]]*test-reviewer[[:space:]]*$'; then
    ok "name: test-reviewer"; else fail "name: test-reviewer in the frontmatter"; fi
if printf '%s\n' "$front" | grep -qE '^description:[[:space:]]*[^[:space:]]'; then
    ok "a description"; else fail "a non-empty description in the frontmatter"; fi
tools=$(printf '%s\n' "$front" | awk '
    /^tools:/ { sub(/^tools:[[:space:]]*/, ""); if ($0 != "") print; inlist = ($0 == ""); next }
    inlist && /^[[:space:]]*-/ { sub(/^[[:space:]]*-[[:space:]]*/, ""); print; next }
    { inlist = 0 }' | tr ',[]' '\n  ' | sed 's/^[[:space:]]*//; s/[[:space:]]*$//' | grep -v '^$')
if [ -z "$tools" ]; then
    fail "a tools list (without one, the subagent inherits every tool, Edit and Write included)"
else
    bad=$(printf '%s\n' "$tools" | grep -vxE 'Read|Grep|Glob' | tr '\n' ' ')
    if [ -z "$bad" ]; then ok "read-only tools ($(echo $tools))"
    else fail "read-only tools: Read, Grep, Glob only (found: $bad)"; fi
fi

# 2. The run: the subagent was launched, and nothing was written.
report=$(uv run --quiet python - "$STREAM" <<'PY'
import json, sys
calls, sub_tools, writes = {}, [], []
for line in open(sys.argv[1], encoding="utf-8"):
    try:
        d = json.loads(line)
    except ValueError:
        continue
    if d.get("type") != "assistant":
        continue
    for c in d.get("message", {}).get("content", []):
        if c.get("type") != "tool_use":
            continue
        name = c.get("name")
        if name in ("Agent", "Task"):
            calls[c.get("id")] = c.get("input", {}).get("subagent_type")
        if d.get("parent_tool_use_id"):
            sub_tools.append((d["parent_tool_use_id"], name))
        if name in ("Edit", "Write", "NotebookEdit"):
            writes.append(name)
ids = [i for i, t in calls.items() if t == "test-reviewer"]
mine = sorted({n for p, n in sub_tools if p in ids})
print("launched" if ids else "not-launched")
print(" ".join(mine) or "-")
print(" ".join(writes) or "-")
PY
)
launched=$(printf '%s\n' "$report" | sed -n 1p)
used=$(printf '%s\n' "$report" | sed -n 2p)
writes=$(printf '%s\n' "$report" | sed -n 3p)
if [ "$launched" = launched ]; then ok "the run launched the test-reviewer subagent"
else fail "the run launched the test-reviewer subagent (no Agent call with subagent_type test-reviewer in $STREAM)"; fi
if [ "$used" = "-" ]; then fail "the subagent used at least one tool (none seen in $STREAM)"
elif printf '%s\n' $used | grep -qvxE 'Read|Grep|Glob'; then fail "the subagent used only Read, Grep, Glob (used: $used)"
else ok "the subagent used only $used"; fi
if [ "$writes" = "-" ]; then ok "no Edit or Write in the run"; else fail "no Edit or Write in the run (found: $writes)"; fi

# 3. The review changed nothing in the code or the tests.
if git diff --quiet exercise-09-start -- src tests && [ -z "$(git ls-files --others --exclude-standard src tests)" ]; then
    ok "src/ and tests/ unchanged since exercise-09-start"
else
    fail "src/ and tests/ unchanged since exercise-09-start"; git diff --stat exercise-09-start -- src tests
fi

if [ "$failed" -eq 0 ]; then echo "All checks passed."; else echo "$failed check(s) failed."; exit 1; fi
