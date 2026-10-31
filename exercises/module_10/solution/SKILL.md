---
name: monthly-export
description: 'Use when accounting asks for the monthly export of the invoices, or whether it is right: "l''export de mars", "vérifie l''export du mois", "monthly export". Checks the TOTAL line of `pachaplan export` against the invoices in the database, then writes the CSV of the month. Not for the payment reminders (that is `relances`).'
argument-hint: '[YYYY-MM]'
allowed-tools: Bash(uv run python ${CLAUDE_SKILL_DIR}/check_export.py *) Bash(mkdir -p exports) Bash(uv run pachaplan export --month * -o exports/*)
---

# Monthly export

The month is `$ARGUMENTS` (`YYYY-MM`). Ask for it if it is missing.

1. Check the export, from the repository root:

   ```bash
   uv run python ${CLAUDE_SKILL_DIR}/check_export.py $ARGUMENTS
   ```

   Exit 0: the TOTAL of the export equals the sum of the invoices of the month. Exit 1:
   they differ; show the line, do not write the export, and stop. Exit 2: the check did
   not run; report the message and stop. Never compute the totals yourself.

2. Only after exit 0, write the CSV:

   ```bash
   mkdir -p exports
   uv run pachaplan export --month $ARGUMENTS -o exports/$ARGUMENTS.csv
   ```

   `-o` overwrites an existing file without warning, and truncates it before reading
   the database: check first that `exports/$ARGUMENTS.csv` does not exist, and ask
   before replacing it. Never point `-o` at a file under `data/`.

3. Report the check line and the path of the file. Nothing is sent from here.
