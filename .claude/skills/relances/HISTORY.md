# History of the relances skill

One entry per change, including the changes tried and dropped. Newest last.

## 2026-11-02: first version, instructions only

Status: replaced the same day.
Why: accounting pasted the same request by hand every Monday.
What it did: 90 lines telling Claude to run `pachaplan unpaid --days 30`, cut the
fixed-width table on its dashes line and add up the balances, with an example of the
expected figures.
Effect: in 24 runs of `claude -p` that used it, the table was right every time (513
reminders, 1 443 848.14), but Claude wrote a throwaway parser in 21 of them, quoted only
the system date in 16 instead of the reference date the tool had used, and four times
gave a total two cents off the table in the sentence above it. The example, labelled
with the wrong date, made a later session conclude that it was false.

## 2026-11-02: the work moves into scripts/relances.py

Status: kept.
Why: what must be right every time (the rule, the totals, the reference date, never
overwriting a file) belongs in code that a test can break, not in prose.
What changed: `SKILL.md` down to the description and how to run the script, without
example figures; the script reuses `planning.unpaid_invoices`, prints its reference
date, refuses an unknown `send ...` action and an existing output file; three tests in
`tests/test_relances_skill.py`, each seen failing on a broken copy of the script.
Effect: checked in fresh sessions, see the next entry.

## 2026-11-02: tested in a fresh session, Skill(relances) allowed

Status: kept.
Why: three `claude -p "prépare les relances de la semaine"` runs in the default
permission mode chose the skill, but the Skill call itself was refused (no allow
rule), and the script, run by hand with `; echo "exit=$?"` after it, needed an
approval that `-p` cannot give. No list came out.
What changed: `Skill(relances)` in the allow rules of `.claude/settings.json`; the
skill says to run the script alone, as written.
Effect: three runs out of three in a fresh session: skill loaded, script run without
a prompt, 513 reminders, reference date 2026-11-02 quoted.
