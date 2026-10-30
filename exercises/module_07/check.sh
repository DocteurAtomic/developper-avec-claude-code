#!/usr/bin/env bash
# Checks the module 7 exercise. Run it from the root of your clone, on your exercise branch:
#   bash <(git show origin/course:exercises/module_07/check.sh)
# Prints one line per check, OK or FAIL, and exits 1 if any check fails.

export PACHAPLAN_TODAY=2026-11-02
base=module-07-end
fails=0
check() {  # check <label> <command...>
    local label=$1; shift
    if "$@" >/dev/null 2>&1; then echo "OK    $label"; else echo "FAIL  $label"; fails=$((fails + 1)); fi
}

commits=$(git rev-list --reverse "$base"..HEAD)
count=$(wc -w <<<"$commits")
first=$(head -n1 <<<"$commits")
check "at least two commits since $base (found $count)" test "$count" -ge 2

first_files=$(git diff-tree --no-commit-id --name-only -r "$first" 2>/dev/null)
added_tests=$(git diff-tree --no-commit-id --name-only --diff-filter=AM -r "$first" -- 'tests/test_*.py' 2>/dev/null)
check "the first commit changes tests, not src/ (found: $(paste -sd' ' <<<"$added_tests"))" \
    bash -c 'test -n "$1" && ! grep -q "^src/" <<<"$2"' _ "$added_tests" "$first_files"

later=$(git log --format=%H "$first"..HEAD -- src/pachaplan/planning.py 2>/dev/null | wc -l)
check "later commits change planning.py (found $later)" test "$later" -ge 1

# The characterization tests must pass on the code they describe: the first commit,
# whose src/ is still the one of module-07-end, checked out in a temporary worktree.
tmp=$(mktemp -d)
if [ -n "$first" ] && git worktree add -q --detach "$tmp/wt" "$first" 2>/dev/null; then
    ( cd "$tmp/wt" && PACHAPLAN_DB="$PWD/data/pachaplan.sqlite" uv run -q pytest -q -p no:cacheprovider $added_tests ) >"$tmp/first.log" 2>&1
    first_code=$?
    git worktree remove --force "$tmp/wt"
else
    first_code=1
fi
rm -rf "$tmp"
check "those tests pass on the code of $base" test "$first_code" -eq 0
check "those tests pass on your last commit" \
    bash -c 'test -n "$1" && PACHAPLAN_DB=data/pachaplan.sqlite uv run -q pytest -q -p no:cacheprovider $1' _ "$added_tests"

out=$(PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q -p no:cacheprovider 2>&1)
code=$?
check "full test suite passes" test "$code" -eq 0
check "no skipped test" bash -c '! grep -q skipped <<<"$1"' _ "$out"

same=1
for pair in 10:a9a714857a97229cf2ccdafb9c190fe1d5d1e06d3049d21abd06c5e17d35fc6f \
            30:4845c0ced38343f05de68e1e2568dceaf360d6e98395694feb1ba732a856d6c8 \
            90:26a65edf5b4e06b802976b5b9546a6b6d4f4f4b61e4c98104c79b11db1ef527d; do
    days=${pair%%:*}
    sum=$(uv run pachaplan unpaid --days "$days" 2>/dev/null | sha256sum | cut -c1-64)
    [ "$sum" = "${pair#*:}" ] || same=0
done
check "unpaid --days 10, 30 and 90 print what they printed at $base" test "$same" -eq 1

length=$(python3 -I - src/pachaplan/planning.py <<'PY'
import ast, sys
tree = ast.parse(open(sys.argv[1], encoding="utf-8").read())
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == "unpaid_invoices":
        first = min([node.lineno] + [d.lineno for d in node.decorator_list])
        print(node.end_lineno - first + 1)
        break
else:
    print(9999)
PY
)
check "unpaid_invoices is under 40 lines (found $length)" test "$length" -lt 40

check "uv run ruff check exits 0" uv run ruff check

if [ "$fails" -eq 0 ]; then echo "All checks passed."; else echo "$fails check(s) failed."; exit 1; fi
