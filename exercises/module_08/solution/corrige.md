# Corrigé de l'exercice du module 8

Ce corrigé suit une exécution réelle, la nuit du 30 au 31 octobre 2026, avec Claude Code
2.1.314 : le prompt de l'énoncé lancé tel quel, puis une demande de correction. Votre agent
cassera le code autrement et écrira d'autres assertions : le critère est le script
`check.sh`. Le patch `solution/fix-three-tests.patch` est une correction possible, à
appliquer sur la branche de départ par `git am`.

## La mesure

```text
$ PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q -rs tests/test_unpaid_report.py | tail -2
SKIPPED [1] tests/test_unpaid_report.py:105: no real database
11 passed, 1 skipped in 0.04s
$ PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q --fail-on-skip; echo "code $?"
[...]
--fail-on-skip: 1 test(s) skipped, failing the run

59 passed, 1 skipped in 0.20s
code 1
```

Onze passés, un sauté, avec la variable. Le message du commit disait douze. Et la commande
de la CI de `module-08-end` sort en 1 : la CI aurait refusé ce commit.

## L'audit de l'agent

Trois minutes, onze tours. L'agent a fait une cassure par test, chacune prouvée par
`grep -nF` puis défaite par `git checkout`, et une de plus pour la sortie vide (la liste des
lignes vidée). Ce qu'il a trouvé :

- `test_unpaid_matches_the_real_database` lit `PACHAPLAN_DATABASE`, que rien ne définit. Il
  est toujours sauté. Avec la bonne variable, il tombe sur une cassure du calcul du solde
  (872 factures au lieu de 370).
- `test_print_unpaid_writes_no_placeholder` ne vérifie que l'absence de `None`. Quand
  `print_unpaid` n'affiche rien, il passe.
- `test_unpaid_second_reminder_after_the_first_one` prend une facture en retard de 61 jours.
  La règle dit « plus de 15 jours » : une cassure à 25, ou à 60, ne le fait pas tomber.
  L'agent a cassé à 70, le test est tombé, et il a écrit à côté que le test ne vérifiait pas
  la limite. Une cassure bien choisie se place sur la limite.

Dans « non vérifié », il a ajouté une remarque juste : la requête de référence du test sur
la vraie base recalcule le solde comme le code qu'elle contrôle. Une erreur commune aux deux
passerait.

## La correction

- Le test sur la vraie base lit `PACHAPLAN_DB`, et son message de saut est celui des autres
  tests sur la vraie base.
- Le test d'affichage vérifie la ligne de FA2, colonne par colonne, et la phrase de résumé.
  L'absence de `None` reste, à côté.
- Le test de la deuxième relance prend deux factures de niveau 1 : 15 jours de retard donnent
  `wait`, 16 donnent `send second reminder`.

```text
$ PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q -rs | tail -1
60 passed in 14.00s
$ bash <(git show origin/course:exercises/module_08/check.sh)
OK    full test suite passes (60 passed in 14.00s)
OK    no skipped test
OK    at least 60 tests (found 60)
OK    the 12 tests of tests/test_unpaid_report.py are still there
OK    break 1 makes a test fail (invoices issued on the cutoff day dropped)
OK    break 2 makes a test fail (print_unpaid prints nothing)
OK    break 3 makes a test fail (second reminder after 25 days instead of 15)
All checks passed.
```

L'agent, lui, a aussi mis à jour le nombre de tests du `CLAUDE.md` (60, et 51 passés et
9 sautés sans la variable), ce que le script ne demande pas mais qu'on attend d'un commit
qui ajoute des tests. Sa version passe le même script.

## Les limites

- Le test sur la vraie base prend une quinzaine de secondes : `unpaid_invoices` lance
  plusieurs requêtes par facture.
- Le délai de paiement (`PAYMENT_TERMS_DAYS`) n'est vérifié que par
  `test_unpaid_due_date_defaults_to_the_payment_terms`. Essayez de le passer à 31, puis
  `git checkout`, puis supprimez les dossiers `__pycache__` de `src/`.
