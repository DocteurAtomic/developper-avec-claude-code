#!/usr/bin/env bash
# Checks the module 14 exercise: five corrections, each written where it will be read.
#
#   bash <(git show origin/course:exercises/module_14/check.sh)
#
# Run it from the root of the project, on your exercice-14 branch. Six checks: the
# preference in your personal CLAUDE.md, the December freeze in the auto memory of this
# project, the lesson in LESSONS.md with its Déclencheur, Preuve and Promu lines, the
# trainers-week skill, the deny rule on uv.lock, and the project itself (tests, ruff, the
# database and uv.lock unchanged). It reads files only: no session is started, nothing
# is written. Your personal files are looked for in $CLAUDE_CONFIG_DIR, or ~/.claude.
set -u
export PACHAPLAN_TODAY=2026-11-02
CFG=${CLAUDE_CONFIG_DIR:-$HOME/.claude}
failed=0
ok()   { printf 'OK    %s\n' "$1"; }
fail() { printf 'FAIL  %s\n' "$1"; failed=$((failed + 1)); }

if [ ! -f pyproject.toml ] || [ ! -f data/pachaplan.sqlite ]; then
    echo "Run this from the root of the pachaplan project." >&2; exit 2
fi

# 1. The preference, in the personal CLAUDE.md.
if [ -f "$CFG/CLAUDE.md" ] && grep -qiE 'relecture|relis|review' "$CFG/CLAUDE.md"; then
    ok "personal CLAUDE.md ($CFG/CLAUDE.md) has the review preference"
else
    fail "no review preference in $CFG/CLAUDE.md"
fi
if git diff module-14-end -- CLAUDE.md | grep '^+' | grep -qiE 'relecture|relis|review'; then
    fail "the review preference is also in the project CLAUDE.md: it is yours, not the team's"
fi

# 2. The December freeze, in the auto memory of this project.
root=$(cd "$(git rev-parse --path-format=absolute --git-common-dir)/.." && pwd)
mem="$CFG/projects/$(printf '%s' "$root" | sed 's/[^A-Za-z0-9]/-/g')/memory"
found=$(python3 -I - "$mem" "$CFG/projects" <<'PY'
import pathlib, re, sys
mem, projects = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
def hit(p):
    t = p.read_text(errors="replace").lower()
    return re.search(r"d[ée]cembre|december", t) and re.search(r"gel|g[èe]le|freez|frozen", t)
here = [p for p in mem.glob("*.md") if p.name != "MEMORY.md" and hit(p)]
if here:
    print("here:" + here[0].name)
else:
    other = [p for p in projects.glob("*/memory/*.md") if p.name != "MEMORY.md" and hit(p)]
    print("other:" + str(other[0]) if other else "none")
PY
)
case "$found" in
    here:*)  ok "auto memory of this project has the December freeze (${found#here:})" ;;
    other:*) fail "the December freeze is in another project's memory: ${found#other:}" ;;
    *)       fail "no memory about the December freeze in $mem" ;;
esac

# 3. The lesson, in LESSONS.md, four lines.
if python3 -I - "$CFG/LESSONS.md" <<'PY'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1])
if not p.exists():
    sys.exit(1)
for entry in re.split(r"(?m)^## ", p.read_text())[1:]:
    low = entry.lower()
    if ("-k" in low or "deselected" in low or "filtre" in low or "filter" in low) \
            and re.search(r"(?m)^d[ée]clencheur\s*:|^trigger\s*:", low) \
            and re.search(r"(?m)^preuve\s*:|^proof\s*:", low) \
            and re.search(r"(?m)^promu\s*:|^promoted\s*:", low):
        sys.exit(0)
sys.exit(1)
PY
then ok "LESSONS.md has the lesson on the empty test filter, with Déclencheur, Preuve, Promu"
else fail "no entry on the empty test filter in $CFG/LESSONS.md (title, Déclencheur, Preuve, Promu)"; fi

# 4. The procedure, as a skill.
skill=.claude/skills/trainers-week/SKILL.md
if [ -f "$skill" ] && python3 -I - "$skill" <<'PY'
import re, sys
t = open(sys.argv[1]).read()
m = re.match(r"---\n(.*?)\n---\n(.*)", t, re.S)
if not m:
    sys.exit(1)
front, body = m.groups()
d = re.search(r"(?m)^description:\s*(.+)", front)
sys.exit(0 if d and len(d.group(1).strip()) > 20 and "trainers" in body else 1)
PY
then ok "skill trainers-week: description and a body that runs pachaplan trainers"
else fail "no $skill with a description and the trainers command"; fi
if git diff module-14-end -- CLAUDE.md | grep '^+' | grep -qiE 'vendredi|friday'; then
    fail "the Friday procedure is also in the project CLAUDE.md, read by every session"
fi

# 5. The ban, as a permission rule.
rule=$(python3 -I - <<'PY'
import json
s = json.load(open(".claude/settings.json")).get("permissions", {})
deny = [r for r in s.get("deny", []) if "uv.lock" in r]
print("edit" if any(r.startswith("Edit(") for r in deny) else ("write" if deny else "none"))
PY
)
case "$rule" in
    edit)  ok "settings.json denies Edit on uv.lock" ;;
    write) fail "the deny rule on uv.lock uses Write(...), which never matches: use Edit(...)" ;;
    *)     fail "no deny rule on uv.lock in .claude/settings.json" ;;
esac

# 6. The project has lost nothing.
out=$(PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q --fail-on-skip 2>&1 | tail -1)
sum=$(sha256sum data/pachaplan.sqlite | cut -c1-64)
if [[ "$out" =~ ^([0-9]+)\ passed ]] && [ "${BASH_REMATCH[1]}" -ge 75 ] && [[ "$out" != *failed* ]] \
        && uv run ruff check > /dev/null 2>&1 \
        && [ "$sum" = 793308b2e47ad90b435cc877819f198f569aa3dc9933650de7f2494c686519c2 ] \
        && git diff --quiet module-14-end -- uv.lock data; then
    ok "project intact: $out, ruff clean, database and uv.lock unchanged"
else
    fail "project: '$out', or ruff, or data/ or uv.lock changed since module-14-end"
fi

if [ "$failed" -eq 0 ]; then echo "All checks passed."; else echo "$failed check(s) failed."; exit 1; fi
