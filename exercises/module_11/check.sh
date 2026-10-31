#!/usr/bin/env bash
# Checks the module 11 exercise on the current branch.
#
#   claude -p "pousse la branche" --output-format stream-json --verbose \
#       < /dev/null > push.jsonl
#   bash <(git show origin/course:exercises/module_11/check.sh) push.jsonl
#
# Run it from the root of the project, on your exercise-11 branch. It reads the hooks
# declared in .claude/settings.json and runs them the way Claude Code does, with a JSON
# event on stdin: the Stop hooks on a red suite and on a green one, the PreToolUse hooks
# on a git push and on a harmless command. Then it reads the stream-json output of the
# session. It does not call claude, and it does not push anything.
#
# The red suite is a temporary test, tests/test_zz_check_red.py, that fails only when
# PACHAPLAN_DB is set, like the integration tests: a Stop hook that runs pytest without
# the variable skips it and lets Claude stop on a red suite. The file is removed on exit.
set -u
STREAM=${1:-}
RED=tests/test_zz_check_red.py
failed=0

ok()   { printf 'OK    %s\n' "$1"; }
fail() { printf 'FAIL  %s\n' "$1"; failed=$((failed + 1)); }

if [ -z "$STREAM" ] || [ ! -s "$STREAM" ]; then
    echo "usage: bash check.sh <stream-json file of the session>" >&2; exit 2
fi
if [ ! -f .claude/settings.json ] || [ ! -f pyproject.toml ]; then
    echo "Run this from the root of the project." >&2; exit 2
fi
if [ -e "$RED" ]; then
    echo "$RED already exists: remove it first." >&2; exit 2
fi
trap 'rm -f "$RED"' EXIT
unset PACHAPLAN_DB

# run_hooks EVENT TOOL JSON: runs every matching handler of EVENT, prints
# "block" if one of them blocks (exit 2, or a JSON decision that blocks), "pass"
# otherwise, and "none" if no handler matches.
run_hooks() {
    uv run --quiet python - "$1" "$2" "$3" <<'PY'
import json, os, re, subprocess, sys

event, tool, payload = sys.argv[1], sys.argv[2], sys.argv[3]
project = os.getcwd()
hooks = json.load(open(".claude/settings.json", encoding="utf-8")).get("hooks", {})

def matches(matcher):
    if matcher in (None, "", "*"):
        return True
    if re.fullmatch(r"[A-Za-z0-9_\- ,|]+", matcher):
        return tool in [m.strip() for m in re.split(r"[|,]", matcher)]
    return re.search(matcher, tool) is not None

found, blocked = False, False
for group in hooks.get(event, []):
    if event != "Stop" and not matches(group.get("matcher")):
        continue
    for h in group.get("hooks", []):
        if h.get("type") != "command":
            continue
        found = True
        env = dict(os.environ, CLAUDE_PROJECT_DIR=project)
        sub = lambda s: s.replace("${CLAUDE_PROJECT_DIR}", project)
        if "args" in h:
            argv = [sub(h["command"])] + [sub(a) for a in h["args"]]
            run = subprocess.run(argv, input=payload, capture_output=True, text=True,
                                 env=env, timeout=h.get("timeout", 600))
        else:
            run = subprocess.run(["sh", "-c", h["command"]], input=payload,
                                 capture_output=True, text=True, env=env,
                                 timeout=h.get("timeout", 600))
        if run.returncode == 2:
            blocked = True
            continue
        try:
            out = json.loads(run.stdout) if run.stdout.strip().startswith("{") else {}
        except ValueError:
            out = {}
        spec = out.get("hookSpecificOutput") or {}
        if out.get("decision") == "block" or spec.get("permissionDecision") == "deny":
            blocked = True
        if out.get("continue") is False:
            blocked = True
print("none" if not found else ("block" if blocked else "pass"))
PY
}

stop_event() {
    printf '{"hook_event_name":"Stop","session_id":"check","cwd":"%s","stop_hook_active":%s,"last_assistant_message":"Done."}' "$PWD" "$1"
}
bash_event() {
    uv run --quiet python -c 'import json, os, sys; print(json.dumps({"hook_event_name": "PreToolUse", "session_id": "check", "cwd": os.getcwd(), "tool_name": "Bash", "tool_input": {"command": sys.argv[1]}}))' "$1"
}

# 1. The suite is green before anything else.
if PACHAPLAN_DB=data/pachaplan.sqlite uv run --quiet pytest -q --fail-on-skip > /dev/null 2>&1; then
    ok "the test suite is green, with PACHAPLAN_DB and --fail-on-skip"
else
    fail "the test suite is green, with PACHAPLAN_DB and --fail-on-skip"
fi

# 2. The Stop hook lets Claude stop on a green suite.
r=$(run_hooks Stop "" "$(stop_event false)")
case $r in
    pass) ok "Stop hook: green suite, stop allowed" ;;
    none) fail "a Stop hook of type command in .claude/settings.json" ;;
    *)    fail "Stop hook: green suite, stop allowed (it blocked)" ;;
esac

# 3. It sends Claude back on a red suite, and 4. lets it go when stop_hook_active is true.
cat > "$RED" <<'EOF'
import os

import pytest


@pytest.mark.skipif(not os.environ.get("PACHAPLAN_DB"), reason="needs PACHAPLAN_DB")
def test_check_red():
    assert False, "red on purpose, written by the module 11 check"
EOF
r=$(run_hooks Stop "" "$(stop_event false)")
if [ "$r" = block ]; then ok "Stop hook: red suite, stop_hook_active false, Claude sent back"
else fail "Stop hook: red suite, stop_hook_active false, Claude sent back (got $r)"; fi
r=$(run_hooks Stop "" "$(stop_event true)")
if [ "$r" = pass ]; then ok "Stop hook: red suite, stop_hook_active true, stop allowed"
else fail "Stop hook: red suite, stop_hook_active true, stop allowed (got $r)"; fi
rm -f "$RED"

# 5. and 6. The PreToolUse hook on Bash.
r=$(run_hooks PreToolUse Bash "$(bash_event 'git -C . push origin HEAD')")
if [ "$r" = block ]; then ok "PreToolUse hook: git -C . push origin HEAD refused"
else fail "PreToolUse hook: git -C . push origin HEAD refused (got $r)"; fi
r=$(run_hooks PreToolUse Bash "$(bash_event 'git status --short')")
if [ "$r" = pass ]; then ok "PreToolUse hook: git status --short allowed"
else fail "PreToolUse hook: git status --short allowed (got $r)"; fi

# 7. The session asked to push got the message of the hook.
report=$(uv run --quiet python - "$STREAM" <<'PY'
import json, re, sys
ids, refused = set(), False
for line in open(sys.argv[1], encoding="utf-8"):
    try:
        d = json.loads(line)
    except ValueError:
        continue
    if d.get("type") == "assistant":
        for c in d.get("message", {}).get("content", []):
            if c.get("type") == "tool_use" and c.get("name") == "Bash":
                if re.search(r"\bgit\b[^;&|\n]*\bpush\b", c.get("input", {}).get("command", "")):
                    ids.add(c.get("id"))
    if d.get("type") == "user":
        content = d.get("message", {}).get("content")
        for c in content if isinstance(content, list) else []:
            if c.get("type") == "tool_result" and c.get("tool_use_id") in ids:
                text = c.get("content")
                text = text if isinstance(text, str) else json.dumps(text)
                if c.get("is_error") and "PreToolUse:Bash hook" in text:
                    refused = True
print("tried" if ids else "not-tried")
print("refused" if refused else "not-refused")
PY
)
if printf '%s\n' "$report" | grep -qx tried && printf '%s\n' "$report" | grep -qx refused; then
    ok "the session tried git push and got the message of the PreToolUse hook"
else
    fail "the session tried git push and got the message of the PreToolUse hook ($(echo $report))"
fi

if [ "$failed" -eq 0 ]; then echo "All checks passed."; exit 0; fi
echo "$failed check(s) failed."; exit 1
