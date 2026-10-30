# Corrigé de l'exercice du module 7

Ce corrigé suit une exécution réelle, la nuit du 30 au 31 octobre 2026, avec Claude Code
2.1.314, les deux prompts de l'énoncé lancés tels quels. Votre agent écrira d'autres tests et
découpera autrement : le critère est le script `check.sh`, et ces fichiers montrent une
exécution parmi d'autres. Les huit commits sont dans `solution/patches/`, à appliquer sur
`module-07-end` par `git am solution/patches/*.patch`.

## Les tests de caractérisation

Cinq minutes et demie, un commit, `Add characterization tests for unpaid_invoices` :

```text
 CLAUDE.md                                          |   9 +-
 .../snapshots/unpaid_invoices/2026-03-15_15d.json  | 209 +++++
 .../snapshots/unpaid_invoices/2026-06-30_90d.json  | 231 ++++++
 .../snapshots/unpaid_invoices/2026-11-02_30d.json  | 874 +++++++++++++++++++++
 tests/test_unpaid_characterization.py              | 332 ++++++++
 tests/test_unpaid_characterization_real.py         |  56 ++
```

Sur la base de test, l'agent a gardé la fixture telle quelle pour quelques appels (30, 10 et
0 jours, une date de référence plus tardive, une liste de types vide), puis ajouté à la copie
temporaire de la base un scénario qui atteint chaque niveau de relance, avec ses seuils
exacts : soixante jours de retard après une mise en demeure donnent encore `wait`, soixante et
un donnent le recouvrement. Les totaux sont comparés avec `pytest.approx`, les lignes
exactement. Sur la vraie base, trois instantanés JSON : (2026-11-02, 30 jours),
(2026-06-30, 90 jours), (2026-03-15, 15 jours). Ils allongent la suite d'une quinzaine de
secondes, la fonction lançant plusieurs requêtes par facture.

```text
$ PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q | tail -1
62 passed in 18.77s
$ uv run pytest -q | tail -1
52 passed, 10 skipped in 0.14s
```

Les comportements figés que l'agent a signalés comme douteux, sans les corriger :

- les paiements sont déduits même s'ils sont datés après le jour demandé, et le niveau de
  relance est lu tel qu'il est aujourd'hui : rejoué à une date passée, le rapport ne montre
  pas l'état de ce jour-là ;
- `balance` est arrondi dans chaque ligne, pas dans les totaux ;
- une facture échue depuis peu, avec une relance déjà envoyée, donne `wait`, et une facture
  pas encore échue `wait (not due yet)` ;
- `today` doit être une date : une chaîne lève `TypeError`, alors qu'`assign_trainers` en
  accepte une.

Il a aussi cassé le code deux fois, pour voir le filet tomber : `> 60` changé en `>= 60`,
trois tests tombent ; le délai de paiement passé à 31 jours, deux tombent.

## Un cache Python périmé

La seconde session a trouvé la suite rouge avant d'écrire une ligne : deux tests de
caractérisation tombaient, avec une échéance au 2 décembre au lieu du 1er. Le code était
juste. La première session, en cassant le délai de paiement (30 changé en 31) puis en le
remettant, avait laissé dans le cache de Python, sous `src/pachaplan/`, un fichier compilé depuis la version
cassée. Python ne recompile un module que si la date de modification ou la taille du source
change ; ici, la modification et sa réparation tenaient dans la même seconde, et 30 et 31 ont
la même longueur. L'agent l'a diagnostiqué et a déplacé les caches. Si une suite tombe sans
raison après une étape de cassure, supprimez les dossiers `__pycache__` du projet avant de
chercher plus loin.

## Le découpage

Sept commits, sept fonctions, `unpaid_invoices` passée de 126 à 32 lignes :

```text
13d0baf Extract the next action of unpaid_invoices into next_action
d2a93e5 Extract the customer lookup of unpaid_invoices into invoice_customer
f4155ef Extract the trainee names of unpaid_invoices into invoice_trainees
2f24add Extract the course title of unpaid_invoices into invoice_course
4d8a762 Extract the payments and credit notes of unpaid_invoices
df2028d Extract the report line of unpaid_invoices into unpaid_row
22252cb Extract the invoice query of unpaid_invoices into invoices_issued_by
```

Ce qui reste dans `unpaid_invoices` : la sélection des factures, le filtre sur le solde, les
totaux, le tri et les cinq plus gros soldes. Les requêtes SQL ont été déplacées sans changer
leur texte. L'agent a noté, sans y toucher, qu'un client introuvable ferait planter
l'affichage (`None[:30]`), et que les requêtes construites par f-strings cassent sur une
apostrophe.

## Le critère

```text
$ bash <(git show origin/course:exercises/module_07/check.sh)
OK    at least two commits since module-07-end (found 8)
OK    the first commit changes tests, not src/ (found: tests/test_unpaid_characterization.py tests/test_unpaid_characterization_real.py)
OK    later commits change planning.py (found 7)
OK    those tests pass on the code of module-07-end
OK    those tests pass on your last commit
OK    full test suite passes
OK    no skipped test
OK    unpaid --days 10, 30 and 90 print what they printed at module-07-end
OK    unpaid_invoices is under 40 lines (found 32)
OK    uv run ruff check exits 0
All checks passed.
```

Une minute vingt, à cause des instantanés de la vraie base. Sur `module-07-end` sans aucun
commit, cinq contrôles échouent. Avec un commit de plus qui change le libellé d'une action
(`send first reminder` en `send a first reminder`), trois échouent : les tests du premier
commit, la suite complète, et la sortie de `unpaid`.
