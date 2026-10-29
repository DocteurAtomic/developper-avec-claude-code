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
uv run pachaplan export --month 2026-10 --format json   # le même export en JSON, pour le tableau de bord de la comptabilité
```

Deux options valent pour toutes les commandes et se placent avant elle :

- `--db CHEMIN` : la base à lire. Par défaut, la variable `PACHAPLAN_DB`, sinon
  `data/pachaplan.sqlite`.
- `--today AAAA-MM-JJ` : la date du jour, pour rejouer un rapport à une date donnée
  (`uv run pachaplan --today 2026-11-02 sessions --below 50`). Par défaut, la variable
  `PACHAPLAN_TODAY`, sinon la date du système.

La base s'ouvre en lecture seule. Une commande qui doit écrire travaille sur une copie
passée par `--db`, jamais sur `data/pachaplan.sqlite`.

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
uv run pachaplan export --month 2026-10 --format json   # the same export as JSON, for the accounting dashboard
```

Two options apply to every command and go before it:

- `--db PATH`: the database to read. Defaults to the `PACHAPLAN_DB` variable, then
  `data/pachaplan.sqlite`.
- `--today YYYY-MM-DD`: the current date, to replay a report as of a given day
  (`uv run pachaplan --today 2026-11-02 sessions --below 50`). Defaults to the
  `PACHAPLAN_TODAY` variable, then the system date.

The database is opened read-only. A command that has to write works on a copy given with
`--db`, never on `data/pachaplan.sqlite`.

### Tests

```bash
uv run pytest -q
uv run ruff check
```

The integration test reads the real database: `PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q`.

### License

MIT, see `LICENSE`.
