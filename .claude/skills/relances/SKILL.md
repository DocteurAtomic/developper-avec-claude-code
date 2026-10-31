---
name: relances
description: 'Use when the user asks to prepare the payment reminders: "prépare les relances", "les relances de la semaine", "qui faut-il relancer", "weekly reminders". Lists the unpaid invoices to remind, grouped by reminder level, with the count and total balance of each group. Prepares the list only, never sends anything. Not for the monthly export (`pachaplan export`).'
allowed-tools: Bash(uv run python ${CLAUDE_SKILL_DIR}/scripts/relances.py *)
---

# Relances

Run the script from the repository root and show its output as is:

```bash
uv run python ${CLAUDE_SKILL_DIR}/scripts/relances.py
```

- Do not recompute the counts or the totals, and do not parse `pachaplan unpaid`
  yourself: the script applies the same rule as the tool.
- Its first line gives the reference date (`PACHAPLAN_TODAY`, then the system date).
  Quote that date; never replace it with today's date.
- The invoices of one level: add `--detail first`, `--detail second` or
  `--detail formal`.
- A CSV file, only when the user asks for one: `-o relances-YYYY-MM-DD.csv`. The
  script refuses to overwrite a file; never delete or rename a file to get around it.
- If the script exits non-zero, report its message and stop.
- Nothing is sent from here. Do not draft reminder letters unless asked.
