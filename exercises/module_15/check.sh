#!/usr/bin/env bash
# Checks the module 15 exercise: a security review of the Claude Code configuration of
# the project, written in SECURITY-REVIEW.md, and the changes it marks "avant de partager".
#
#   bash <(git show origin/course:exercises/module_15/check.sh)
#
# Run it from the root of the project, on your exercice-15 branch. Six checks: the seven
# sections of the review, the six fields of every finding, the seven points that a review of
# this configuration cannot miss, the changes marked "avant de partager" applied, the
# settings still valid, and the project intact (tests, ruff, the database). It reads files
# and runs the tests: no Claude Code session is started. It judges the form and the
# coverage of the review; the grid of the statement judges the reasons.
set -u
export PACHAPLAN_TODAY=2026-11-02
BASE=${BASE:-module-15-end}
REVIEW=SECURITY-REVIEW.md
failed=0
ok()   { printf 'OK    %s\n' "$1"; }
fail() { printf 'FAIL  %s\n' "$1"; failed=$((failed + 1)); }

if [ ! -f pyproject.toml ] || [ ! -f data/pachaplan.sqlite ]; then
    echo "Run this from the root of the pachaplan project." >&2; exit 2
fi
if ! git rev-parse -q --verify "$BASE^{commit}" >/dev/null; then
    echo "No $BASE here: git fetch --tags, or start from git switch -c exercice-15 module-15-end." >&2; exit 2
fi
if [ ! -f "$REVIEW" ]; then
    fail "no $REVIEW at the root of the project (template: git show origin/course:exercises/module_15/$REVIEW)"
    echo "$failed check(s) failed."; exit 1
fi

# 1 to 4: the review itself, parsed once.
python3 -I - "$REVIEW" "$BASE" <<'PY'
import pathlib, re, subprocess, sys
review, base = sys.argv[1], sys.argv[2]
text = pathlib.Path(review).read_text()
SECTIONS = ["Permissions", "Bac à sable", "Hooks", "Serveur MCP", "Skill et sous-agent",
            "Automatisation", "Le poste et le dépôt"]
LEGS = {"données privées", "contenu non fiable", "sortie", "exécution"}
HELD = {"mécanique", "consigne", "rien"}
DECISIONS = {"avant de partager", "accepté", "plus tard"}
FIELDS = ["Fichier", "Permet", "Jambe", "Tenu par", "Décision", "Changement"]

def starts(value, allowed):
    """The value opens with one of the allowed terms; an explanation may follow."""
    v = value.strip(" `").lower()
    return any(v.startswith(a) for a in allowed)

def out(ok, msg):
    print(("OK    " if ok else "FAIL  ") + msg)
    return 0 if ok else 1

failed = 0
sections = {}
for block in re.split(r"(?m)^## ", text)[1:]:
    title, _, body = block.partition("\n")
    sections[title.strip()] = body
missing = [s for s in SECTIONS if s not in sections]
empty = [s for s in SECTIONS if s in sections and not re.search(r"(?m)^### ", sections[s])]
failed += out(not missing and not empty,
              "the seven sections, each with at least one finding"
              + (f" (missing: {', '.join(missing)})" if missing else "")
              + (f" (no finding under: {', '.join(empty)})" if empty else ""))

findings, problems = [], []
for name in SECTIONS:
    for block in re.split(r"(?m)^### ", sections.get(name, ""))[1:]:
        title, _, body = block.partition("\n")
        f = {"title": title.strip()}
        for field in FIELDS:
            m = re.search(rf"(?m)^- {field} ?: *(.+)$", body)
            f[field] = m.group(1).strip() if m else ""
        findings.append(f)
        bad = [x for x in FIELDS if not f[x] or f[x].startswith("<")]
        legs = [x.strip(" `").lower() for x in f["Jambe"].split("(")[0].split(",")]
        if not all(starts(x, LEGS) for x in legs): bad.append("Jambe")
        if not starts(f["Tenu par"], HELD): bad.append("Tenu par")
        if not starts(f["Décision"], DECISIONS): bad.append("Décision")
        m = re.search(r"`([^`]+)`", f["Fichier"])
        path = f["Fichier"] = (m.group(1) if m else f["Fichier"]).strip()
        if path and not path.startswith("~") and not pathlib.Path(path).exists():
            bad.append(f"Fichier {path} n'existe pas")
        if bad:
            problems.append(f"« {f['title']} » : {', '.join(sorted(set(bad)))}")
failed += out(len(findings) >= 10 and not problems,
              f"{len(findings)} findings, every one with its six fields (at least 10 expected)"
              + ("".join("\n        " + p for p in problems[:8])))

low = text.lower()
POINTS = [
    ("git push", r"git push[^\n]*(-c |forme|texte|écrit|text|contourn)|(-c |forme|texte|contourn)[^\n]*git push"),
    ("the mcp__pachaplan__* wildcard", r"mcp__pachaplan__\*"),
    ("hooks or .mcp.json run by claude -p before any trust",
     r"(-p|non interactif)[^\n]*(confiance|trust|approuv)|(confiance|trust|approuv)[^\n]*(-p\b|non interactif)"),
    ("the .env variants (.env.local)", r"\.env\.(local|\*)"),
    ("settings.local.json and the .gitignore of the project", r"settings\.local\.json"),
    ("the network in auto mode, or the fallback without bubblewrap",
     r"failifunavailable|repli|fallback|classifieur|strictallowlist"),
    ("the virtual environment written in the sandbox, run outside it", r"\.venv|site-packages"),
]
miss = [name for name, rx in POINTS if not re.search(rx, low)]
failed += out(not miss, "the seven points of the grid are in the review"
              + (f" (not found: {'; '.join(miss)})" if miss else ""))

before = [f for f in findings if f["Décision"].lower() == "avant de partager"]
unapplied = []
for f in before:
    path = f["Fichier"]
    if path.startswith("~"):
        continue
    same = subprocess.run(["git", "diff", "--quiet", base, "--", path]).returncode == 0
    untracked = subprocess.run(["git", "ls-files", "--error-unmatch", path],
                               capture_output=True).returncode != 0
    if same and not untracked:
        unapplied.append(f"« {f['title']} » ({path} unchanged since {base})")
failed += out(len(before) >= 2 and not unapplied,
              f"{len(before)} changes marked « avant de partager », each one applied"
              + ("".join("\n        " + u for u in unapplied)))
sys.exit(failed)
PY
failed=$((failed + $?))

# 5. The settings still load, and no rule that never matches.
if python3 -I - .claude/settings.json <<'PY'
import json, re, sys
d = json.load(open(sys.argv[1]))
rules = [r for k in ("allow", "ask", "deny") for r in d.get("permissions", {}).get(k, [])]
bad = [r for r in rules if re.match(r"(Write|NotebookEdit|Glob)\(", r)]
if bad:
    print("        rules that never match: " + ", ".join(bad)); sys.exit(1)
PY
then ok ".claude/settings.json is valid JSON, no Write(...) or Glob(...) path rule"
else fail ".claude/settings.json does not load, or has a path rule that never matches (use Edit or Read)"; fi

# 6. The project itself.
passed=$(PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q --fail-on-skip 2>&1 | tail -1)
sha=$(sha256sum data/pachaplan.sqlite | cut -c1-64)
if [[ "$passed" =~ ^[0-9]+\ passed ]] && ! [[ "$passed" =~ failed|skipped|error ]] \
    && uv run ruff check -q >/dev/null 2>&1 \
    && [ "$sha" = 793308b2e47ad90b435cc877819f198f569aa3dc9933650de7f2494c686519c2 ] \
    && git diff --quiet "$BASE" -- data; then
    ok "project intact: $passed, ruff clean, database unchanged"
else
    fail "project not intact: tests \"$passed\", ruff, or data/ changed"
fi

if [ "$failed" -eq 0 ]; then echo "All checks passed."; else echo "$failed check(s) failed."; fi
[ "$failed" -eq 0 ]
