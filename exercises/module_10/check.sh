#!/usr/bin/env bash
# Checks the module 10 exercise on the current branch.
#
#   claude -p "/monthly-export 2026-03" --output-format stream-json --verbose \
#       < /dev/null > export.jsonl
#   bash <(git show origin/course:exercises/module_10/check.sh) export.jsonl
#
# Run it from the root of the project, on your exercise-10 branch. It runs the
# check script of the skill here and in a temporary worktree at module-05-start,
# where the end of month is still wrong, then reads the stream-json output of the
# session. It does not call claude.
set -u
SKILL=.claude/skills/monthly-export
SCRIPT=$SKILL/check_export.py
STREAM=${1:-}
failed=0

ok()   { printf 'OK    %s\n' "$1"; }
fail() { printf 'FAIL  %s\n' "$1"; failed=$((failed + 1)); }

if [ -z "$STREAM" ] || [ ! -s "$STREAM" ]; then
    echo "usage: bash check.sh <stream-json file of the session>" >&2; exit 2
fi
if ! git rev-parse -q --verify module-05-start >/dev/null; then
    echo "The tag module-05-start is missing: fetch the tags of the course repository." >&2
    exit 2
fi

# 1. The skill and its script.
if [ -f "$SKILL/SKILL.md" ]; then ok "$SKILL/SKILL.md exists"; else fail "$SKILL/SKILL.md exists"; fi
if [ -f "$SCRIPT" ]; then ok "$SCRIPT exists"; else fail "$SCRIPT exists"; fi

# 2. The script agrees with the database on the current branch.
uv run --quiet python "$SCRIPT" 2026-03 > /dev/null 2>&1
code=$?
if [ "$code" -eq 0 ]; then ok "exit 0 on 2026-03 here"; else fail "exit 0 on 2026-03 here (got $code)"; fi

# 3. It catches the old end of month, in a worktree at module-05-start.
abs=$(realpath "$SCRIPT")
tmp=$(mktemp -d)
if git worktree add -q "$tmp/m05" module-05-start 2>/dev/null; then
    (cd "$tmp/m05" && uv run --quiet python "$abs" 2026-03 > /dev/null 2>&1)
    code=$?
    git worktree remove --force "$tmp/m05"
    if [ "$code" -eq 1 ]; then ok "exit 1 on 2026-03 at module-05-start"
    else fail "exit 1 on 2026-03 at module-05-start (got $code)"; fi
else
    fail "a temporary worktree at module-05-start"
fi
rm -rf "$tmp"

# 4. A fresh session loaded the skill and ran its script.
report=$(uv run --quiet python - "$STREAM" <<'PY'
import json, sys
skills, ran, result = [], False, ""
ids = set()
for line in open(sys.argv[1], encoding="utf-8"):
    try:
        d = json.loads(line)
    except ValueError:
        continue
    if d.get("type") == "system" and d.get("subtype") == "init":
        skills = d.get("skills") or []
    if d.get("type") == "assistant":
        for c in d.get("message", {}).get("content", []):
            if c.get("type") == "tool_use" and c.get("name") == "Bash":
                if "monthly-export/check_export.py" in c.get("input", {}).get("command", ""):
                    ids.add(c.get("id"))
    if d.get("type") == "user":
        content = d.get("message", {}).get("content")
        for c in content if isinstance(content, list) else []:
            if c.get("type") == "tool_result" and c.get("tool_use_id") in ids:
                text = c.get("content")
                text = text if isinstance(text, str) else json.dumps(text)
                if "2026-03" in text and "OK" in text and not c.get("is_error"):
                    ran = True
print("loaded" if "monthly-export" in skills else "not-loaded")
print("ran" if ran else "not-ran")
PY
)
if printf '%s\n' "$report" | grep -qx loaded; then ok "the session listed the monthly-export skill"
else fail "the session listed the monthly-export skill"; fi
if printf '%s\n' "$report" | grep -qx ran; then ok "the session ran check_export.py 2026-03, OK"
else fail "the session ran check_export.py 2026-03 and got its OK line"; fi

if [ "$failed" -eq 0 ]; then echo "All checks passed."; exit 0; fi
echo "$failed check(s) failed."; exit 1
