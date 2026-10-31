#!/usr/bin/env bash
# Checks the module 8 exercise on the current branch.
#
#   bash <(git show origin/course:exercises/module_08/check.sh)
#
# Run it from the root of the project, on your exercise-08 branch, with your fix committed
# or not. It changes src/pachaplan/planning.py three times, one break at a time, and puts
# it back with git checkout; src/ must be unchanged when it starts.
set -u
export PACHAPLAN_TODAY=2026-11-02
PLANNING=src/pachaplan/planning.py
FILE=tests/test_unpaid_report.py
EXPECTED=60
failed=0

ok()   { printf 'OK    %s\n' "$1"; }
fail() { printf 'FAIL  %s\n' "$1"; failed=$((failed + 1)); }

if ! git rev-parse -q --verify module-08-end >/dev/null; then
    echo "The tag module-08-end is missing: git fetch --tags origin" >&2; exit 2
fi
if ! git diff --quiet module-08-end -- src; then
    echo "src/ differs from module-08-end: the exercise fixes the tests, not the code." >&2
    git diff --stat module-08-end -- src >&2; exit 2
fi
restore() { git checkout -q -- "$PLANNING"; find src -name __pycache__ -type d -exec rm -rf {} +; }
trap restore EXIT

# 1. The suite with the real database: the number of tests, nothing skipped.
out=$(PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q -rs -p no:cacheprovider 2>&1)
code=$?
summary=$(printf '%s\n' "$out" | tail -1)
passed=$(printf '%s\n' "$summary" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+')
if [ "$code" -eq 0 ]; then ok "full test suite passes ($summary)"; else fail "full test suite passes ($summary)"; fi
if printf '%s\n' "$summary" | grep -q skipped; then fail "no skipped test ($summary)"; else ok "no skipped test"; fi
if [ "${passed:-0}" -ge "$EXPECTED" ]; then ok "at least $EXPECTED tests (found ${passed:-0})"
else fail "at least $EXPECTED tests (found ${passed:-0})"; fi

# 2. The twelve tests of the file are still there: a test is fixed, not deleted.
names=$(git show "exercise-08-start:$FILE" 2>/dev/null | grep -oE '^def (test_[a-z0-9_]+)' | cut -c5-)
if [ -z "$names" ]; then
    names=$(grep -oE '^def (test_[a-z0-9_]+)' "$FILE" | cut -c5-)
    echo "note: tag exercise-08-start not found, checking the names of the current file" >&2
fi
missing=""
for n in $names; do grep -qE "^def $n\(" "$FILE" || missing="$missing $n"; done
if [ -z "$missing" ]; then ok "the $(echo $names | wc -w) tests of $FILE are still there"
else fail "tests deleted or renamed:$missing"; fi

# 3. Three breaks of the code, each must make at least one test fail.
breaks=(
    "s/i.invoice_date <= '/i.invoice_date < '/"
    '/^def print_unpaid/a\    return'
    "s/level == 1 and days_late > 15/level == 1 and days_late > 25/"
)
proofs=(
    "i.invoice_date < '"
    "^    return$"
    "days_late > 25"
)
labels=(
    "invoices issued on the cutoff day dropped"
    "print_unpaid prints nothing"
    "second reminder after 25 days instead of 15"
)
for i in 0 1 2; do
    restore
    sed -i "${breaks[$i]}" "$PLANNING"
    if ! grep -qE -- "${proofs[$i]}" "$PLANNING" || git diff --quiet -- "$PLANNING"; then
        fail "break $((i + 1)) could not be applied (${labels[$i]})"; continue
    fi
    if PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q -p no:cacheprovider >/dev/null 2>&1; then
        fail "break $((i + 1)) makes a test fail (${labels[$i]}): the suite stays green"
    else
        ok "break $((i + 1)) makes a test fail (${labels[$i]})"
    fi
done
restore
trap - EXIT

if [ "$failed" -eq 0 ]; then echo "All checks passed."; else echo "$failed check(s) failed."; exit 1; fi
