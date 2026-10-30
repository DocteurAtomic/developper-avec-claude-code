# Corrigé de l'exercice du module 3

## Le CLAUDE.md

`corrige/CLAUDE.md` ajoute au fichier de `module-03-end` la date du gel :

```markdown
## Planning date

- Reports are computed as of 2026-11-02, the freeze date of the November planning
  (planning team, 2026-10-29). Run every report with `--today 2026-11-02`, or with
  `PACHAPLAN_TODAY=2026-11-02` in the environment: the system date gives other numbers.
```

et, dans « Conventions » :

```markdown
- Every new CLI option gets a test in `tests/test_cli.py`, in the same commit.
```

La règle sur la date dit qui l'a décidée et quand : en décembre, la session qui la lira
saura qu'elle date du gel de novembre, et vous saurez qu'il faut la changer. Elle donne les
deux façons de passer la date, parce que l'agent choisit l'une ou l'autre selon la commande.

Répété le 30 octobre 2026 : avec ce fichier, l'agent lance
`uv run pachaplan --today 2026-11-02 sessions --below 50` et répond 80 ; sans lui, il lance
`uv run pachaplan sessions --below 50` et répond 66.

## Le README

`corrige/README.md` supprime les deux lignes `export --month 2026-10 --format json`, en
français et en anglais. L'export JSON n'existe pas dans `cli.py` : le documenter ferait
lancer à l'agent une commande qui sort en code 2. Si l'équipe veut cet export, c'est un
ticket, pas une ligne de documentation.

## Les coupes dans le fichier de /init

Le fichier de `/init` de la répétition 1 faisait 82 lignes (1,7 k tokens à chaque session),
celui de `module-03-end` en fait 23.

| Coupé | Raison |
|---|---|
| « This file provides guidance to Claude Code... » | ne dit rien du projet |
| « What this is » : description du projet | dans le `README`, que l'agent lit |
| `uv sync`, `uv run pachaplan --help` | évident, dans le `README` |
| `uv run pytest -q tests/test_unpaid.py::test_name` | faux : aucun test de ce nom, code 4 |
| `uv run pytest -q` seul | remplacé par la suite complète, la seule à lancer |
| « Architecture » : les trois modules et leurs fonctions | l'agent le trouve en lisant `src/`, et ce sera faux au premier remaniement |
| Conventions du domaine (statuts, inscriptions, avoirs, salle 43) | dans les constantes de `planning.py` ; utiles pour une tâche, pas pour chaque session |
| SQL en f-strings, requêtes N+1 | un défaut connu va au suivi des tickets |
| « Tests » : la fixture et `conftest.py` | l'agent les trouve par `conftest.py` ; gardé en une ligne |
| Rappel des règles de `.claude/settings.json` | déjà imposé par les réglages |
| « Known discrepancies » : `--format json`, fin de mois à +30 jours | des défauts : on les corrige ou on ouvre un ticket |

Ce qui a été gardé ou ajouté :

- la suite complète avec `PACHAPLAN_DB`, le nombre de tests, et l'incident daté qui en
  a fait une règle ;
- `uv run ruff check` avec ce qu'il rend aujourd'hui (5 erreurs, code 1) ;
- la base jamais écrite, et la copie par `--db` ;
- la langue du code et des commits, que l'agent ne devine pas quand on lui parle français.
