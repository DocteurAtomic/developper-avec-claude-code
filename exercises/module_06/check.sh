#!/usr/bin/env bash
# Checks the module 6 exercise. Run it from the root of your clone, on your exercise branch:
#   bash <(git show origin/course:exercises/module_06/check.sh)
# Prints one line per check, OK or FAIL, and exits 1 if any check fails.

export PACHAPLAN_TODAY=2026-11-02
fails=0
check() {  # check <label> <command...>
    local label=$1; shift
    if "$@" >/dev/null 2>&1; then echo "OK    $label"; else echo "FAIL  $label"; fails=$((fails + 1)); fi
}

merges=$(git log --merges --oneline module-06-start..HEAD | wc -l)
reverts=$(git log --oneline module-06-start..HEAD | grep -c 'Revert')
trees=$(git worktree list | wc -l)

check "two merge commits since module-06-start (found $merges)" test "$merges" -eq 2
check "at least one revert commit (found $reverts)" test "$reverts" -ge 1
check "git worktree list shows the main checkout only (found $trees)" test "$trees" -eq 1
check "worktree.baseRef is \"head\" in .claude/settings.json" \
    python3 -I -c 'import json, sys; sys.exit(json.load(open(".claude/settings.json")).get("worktree", {}).get("baseRef") != "head")'

out=$(PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q 2>&1)
code=$?
check "full test suite passes" test "$code" -eq 0
check "no skipped test" bash -c '! grep -q skipped <<<"$1"' _ "$out"

check "unpaid --days 30 prints what it printed at module-06-start" bash -c \
    'test "$(uv run pachaplan unpaid --days 30 | sha256sum | cut -c1-64)" = 4845c0ced38343f05de68e1e2568dceaf360d6e98395694feb1ba732a856d6c8'

report=$(uv run pachaplan sessions --below 50)
ids=$(awk '$2 ~ /^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]$/ {print $1}' <<<"$report" | paste -sd, -)
expected=$(sqlite3 -readonly data/pachaplan.sqlite \
    "SELECT 'domain ' || c.domain_code || ': ' || COUNT(*) FROM session s JOIN course c ON c.course_id = s.course_id
     WHERE s.session_id IN (${ids:-0}) GROUP BY c.domain_code ORDER BY c.domain_code")
actual=$(grep '^domain ' <<<"$report")
check "sessions --below 50 ends with one line per domain, counts from sqlite3" \
    bash -c 'test -n "$1" && test "$1" = "$2"' _ "$actual" "$expected"

if [ "$fails" -eq 0 ]; then echo "All checks passed."; else echo "$fails check(s) failed."; exit 1; fi
