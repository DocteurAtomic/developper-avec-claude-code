# pachaplan

Outil de planification de PachaData. The English version follows the French one.

## Français

`pachaplan` est l'outil en ligne de commande du service planification de PachaData,
société de formation fictive. Il lit une base SQLite (`data/pachaplan.sqlite`) qui contient
le catalogue, les sessions de 2025 à 2027, les formateurs, les inscriptions, les factures et
les paiements. Les personnes et les sociétés sont fictives, les adresses électroniques sont
sur le domaine réservé `.example`.

### Installer

Il faut `uv` (https://docs.astral.sh/uv/). Il installe Python 3.13 et les dépendances :

```bash
uv sync
uv run pachaplan --help
```

### Les commandes

```bash
uv run pachaplan sessions --below 50          # sessions à venir remplies à moins de 50 %
uv run pachaplan trainers --date 2026-11-18   # formateurs en session ce jour-là
uv run pachaplan unpaid --days 30             # factures émises il y a 30 jours ou plus et non soldées
uv run pachaplan export --month 2026-10       # lignes de facture du mois, en CSV
uv run pachaplan export --month 2026-10 -o 2026-10.csv   # le même export écrit dans un fichier CSV
```

Deux options valent pour toutes les commandes et se placent avant elle :

- `--db CHEMIN` : la base à lire. Par défaut, la variable `PACHAPLAN_DB`, sinon
  `data/pachaplan.sqlite`.
- `--today AAAA-MM-JJ` : la date du jour, pour rejouer un rapport à une date donnée
  (`uv run pachaplan --today 2026-11-02 sessions --below 50`). Par défaut, la variable
  `PACHAPLAN_TODAY`, sinon la date du système.

La base s'ouvre en lecture seule. Une commande qui doit écrire travaille sur une copie
passée par `--db`, jamais sur `data/pachaplan.sqlite`.

### Les relances

Les relances de la semaine (factures à relancer, par niveau, avec leur nombre et leur
solde) sortent d'un script, que le skill `relances` de Claude Code lance aussi
(`/relances`, ou « prépare les relances de la semaine ») :

```bash
uv run python .claude/skills/relances/scripts/relances.py                 # le résumé par niveau
uv run python .claude/skills/relances/scripts/relances.py --detail second # les factures d'un niveau
uv run python .claude/skills/relances/scripts/relances.py -o relances.csv # la liste dans un fichier neuf
```

Le script n'écrase jamais un fichier existant et n'envoie rien.

### Le serveur MCP

`pachaplan-mcp` répond aux questions de planification pour un agent comme Claude Code,
sans lui ouvrir le shell. Il tourne en local (stdio) et expose deux outils en lecture
seule : les sessions qui commencent dans une semaine, et la charge d'un formateur sur un
mois. Le fichier `.mcp.json` le déclare pour le projet ; Claude Code demande de
l'approuver à la première session.

```bash
uv run pachaplan-mcp                      # le serveur, sur data/pachaplan.sqlite
claude mcp get pachaplan                  # son état dans Claude Code
```

Chaque connexion du serveur refuse toute écriture, `ATTACH` compris.

### Les automatismes

`scripts/monday-note.sh` prépare la note du lundi du service planification par
`claude -p` (dans `reports/`, ignoré par Git). Le workflow
`.github/workflows/claude-review.yml` relit chaque pull request ; il demande le secret
`CLAUDE_CODE_OAUTH_TOKEN`.

### Les tests

```bash
uv run pytest -q
uv run ruff check
```

Le test d'intégration lit la vraie base : `PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q`.

### Licence

MIT, voir `LICENSE`.

## English

`pachaplan` is the command line tool of the planning team at PachaData, a fictional
training company. It reads a SQLite database (`data/pachaplan.sqlite`) holding the catalog,
the sessions from 2025 to 2027, the trainers, the enrollments, the invoices and the
payments. People and companies are fictional, e-mail addresses use the reserved `.example`
domain.

### Install

You need `uv` (https://docs.astral.sh/uv/). It installs Python 3.13 and the dependencies:

```bash
uv sync
uv run pachaplan --help
```

### Commands

```bash
uv run pachaplan sessions --below 50          # upcoming sessions filled under 50%
uv run pachaplan trainers --date 2026-11-18   # trainers teaching on that day
uv run pachaplan unpaid --days 30             # invoices issued 30 days ago or more, still open
uv run pachaplan export --month 2026-10       # invoice lines of the month, as CSV
uv run pachaplan export --month 2026-10 -o 2026-10.csv   # the same export written to a CSV file
```

Two options apply to every command and go before it:

- `--db PATH`: the database to read. Defaults to the `PACHAPLAN_DB` variable, then
  `data/pachaplan.sqlite`.
- `--today YYYY-MM-DD`: the current date, to replay a report as of a given day
  (`uv run pachaplan --today 2026-11-02 sessions --below 50`). Defaults to the
  `PACHAPLAN_TODAY` variable, then the system date.

The database is opened read-only. A command that has to write works on a copy given with
`--db`, never on `data/pachaplan.sqlite`.

### Payment reminders

This week's reminders (invoices to remind, by level, with their count and balance) come
from a script, which the `relances` skill of Claude Code also runs (`/relances`, or
"prepare this week's reminders"):

```bash
uv run python .claude/skills/relances/scripts/relances.py                 # summary by level
uv run python .claude/skills/relances/scripts/relances.py --detail second # invoices of one level
uv run python .claude/skills/relances/scripts/relances.py -o relances.csv # the list in a new file
```

The script never overwrites an existing file and sends nothing.

### The MCP server

`pachaplan-mcp` answers planning questions for an agent such as Claude Code, without
giving it a shell. It runs locally (stdio) and exposes two read-only tools: the sessions
starting in a week, and the load of a trainer over a month. `.mcp.json` declares it for
the project; Claude Code asks you to approve it in the first session.

```bash
uv run pachaplan-mcp                      # the server, on data/pachaplan.sqlite
claude mcp get pachaplan                  # its status in Claude Code
```

Every connection of the server refuses any write, `ATTACH` included.

### Automation

`scripts/monday-note.sh` prepares the Monday note of the planning team with `claude -p`
(in `reports/`, ignored by Git). The `.github/workflows/claude-review.yml` workflow
reviews every pull request; it needs the `CLAUDE_CODE_OAUTH_TOKEN` secret.

### Tests

```bash
uv run pytest -q
uv run ruff check
```

The integration test reads the real database: `PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q`.

### License

MIT, see `LICENSE`.
