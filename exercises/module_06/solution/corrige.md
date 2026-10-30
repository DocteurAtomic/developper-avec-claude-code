# Corrigé de l'exercice du module 6

Ce corrigé suit une exécution réelle, le 30 octobre 2026, avec Claude Code 2.1.314. Votre
agent écrira un autre code : le critère est le script `check.sh`, et ces fichiers montrent
une exécution parmi d'autres. Les deux commits de l'agent sont dans
`solution/domains.patch` et `solution/unpaid-newest-first.patch`.

## Le réglage

```bash
git switch -c exercice-06 module-06-start
python3 -I - <<'PY'
import json
p = ".claude/settings.json"
d = json.load(open(p))
d["worktree"] = {"baseRef": "head"}
open(p, "w").write(json.dumps(d, indent=2) + "\n")
PY
git commit -am "Branch new worktrees from the local HEAD"
```

## Les deux worktrees

Les deux sessions sont parties du commit du réglage (`git log --oneline -2` dans chacune).

Le worktree `domaines` a ajouté `domain_code` à la requête de `upcoming_sessions`, une clé
`domain` à chaque ligne de `low_fill_sessions`, et dans `print_low_fill`, après la ligne de
total, une ligne vide puis une ligne par domaine. Un test dans `tests/test_sessions.py`. Avec la
base du cours :

```text
80 session(s) under 50.0% between 2026-11-02 and 2026-12-02.

domain AI: 2
domain BI: 8
domain CL: 11
domain CO: 6
domain DB: 30
domain DV: 7
domain MG: 6
domain PM: 6
domain SC: 4
```

Le worktree `recentes` a changé la clé de tri de `unpaid_invoices` (date décroissante, puis
numéro de facture) et ajouté un test dans `tests/test_unpaid.py`, qui insère deux factures dans
sa copie de la base de test. L'agent a prévenu de lui-même que l'ancien tri mettait les plus
gros retards en tête, ce qui servait peut-être aux relances : c'est la raison du revert.

## Les fusions et le revert

```bash
git show --stat worktree-domaines
git show --stat worktree-recentes
git merge --no-ff worktree-domaines
git merge --no-ff worktree-recentes
git revert worktree-recentes        # le commit du tri, pas la fusion
```

`git revert worktree-recentes` vise le dernier commit de la branche, le tri, qui est un commit
ordinaire. Annuler la fusion elle-même demanderait `git revert -m 1 <fusion>`, et une fusion
annulée se refait mal : Git considère ensuite la branche comme déjà intégrée.

L'exécution du corrigé est passée sans conflit : les agents avaient laissé `CLAUDE.md`
intact, et les deux modifications de `planning.py` étaient éloignées.

## Le nettoyage

```bash
git log --oneline --graph module-06-start..     # les deux commits sont sur exercice-06
git worktree list
git worktree remove .claude/worktrees/domaines
git worktree remove .claude/worktrees/recentes
git branch -d worktree-domaines worktree-recentes
```

En session interactive, `/exit` propose de supprimer le worktree et le fait. Lancé par
`claude -p --worktree`, le worktree reste verrouillé : `git worktree unlock` avant
`git worktree remove`.

```text
* 9268926 Revert "Sort the unpaid report by invoice date, newest first, then invoice code"
*   70a27c9 Merge branch 'worktree-recentes' into exercice-06
|\
| * 3ecf0a0 Sort the unpaid report by invoice date, newest first, then invoice code
* |   ddfcd04 Merge branch 'worktree-domaines' into exercice-06
|\ \
| |/
|/|
| * 51cb294 Count the listed sessions per domain at the end of the low fill report
|/
* 2baf753 Branch new worktrees from the local HEAD
```

## Le critère

```text
$ bash <(git show origin/course:exercises/module_06/check.sh)
OK    two merge commits since module-06-start (found 2)
OK    at least one revert commit (found 1)
OK    git worktree list shows the main checkout only (found 1)
OK    worktree.baseRef is "head" in .claude/settings.json
OK    full test suite passes
OK    no skipped test
OK    unpaid --days 30 prints what it printed at module-06-start
OK    sessions --below 50 ends with one line per domain, counts from sqlite3
All checks passed.
```

14 tests passent avec la base : les 13 du départ et celui des domaines ; le test du tri est
parti avec le revert. Sans le revert, deux contrôles échouent ; avec un worktree oublié, un.
