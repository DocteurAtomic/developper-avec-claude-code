# Exercice du module 7

La comptabilité doit bientôt demander une évolution du rapport des impayés, et `unpaid_invoices`
fait cent vingt-six lignes, avec plusieurs requêtes par facture et une cascade de conditions pour
choisir la relance. Avant que quelqu'un y touche, l'équipe veut un filet, puis une fonction
découpée. Le rapport, lui, ne doit pas changer d'un octet.

## Le départ

Partez de l'étiquette `module-07-end`, la fin du module : `ruff` y sort en code 0, et le
critère l'exige.

```bash
git switch -c exercice-07 module-07-end
uv sync
export PACHAPLAN_TODAY=2026-11-02
git status          # doit être vide
```

Pour mesurer la longueur d'une fonction pendant le travail, récupérez le script fourni, hors du
dépôt :

```bash
git show origin/course:exercises/module_07/tools/function_length.py > ../function_length.py
uv run python ../function_length.py src/pachaplan/planning.py unpaid_invoices
```

Au départ : `unpaid_invoices: 126 lines`.

## Les consignes

1. Gardez une trace du rapport tel qu'il est, hors du dépôt :

   ```bash
   uv run pachaplan unpaid --days 30 > ../unpaid-avant.txt
   ```

2. Dans une session `claude`, faites écrire les tests de caractérisation de
   `unpaid_invoices`, sans toucher au code de l'application. Sur la base de test, et sur
   quelques couples de date et de nombre de jours de la vraie base, dans un fichier qui se
   saute sans `PACHAPLAN_DB`. Un prompt possible :

   ```text
   Avant de toucher à unpaid_invoices dans src/pachaplan/planning.py, écris des tests de caractérisation : ce qu'elle rend aujourd'hui, juste ou faux, sur la base de test, et sur deux ou trois couples de date et de nombre de jours sur la vraie base, dans un fichier qui se saute sans PACHAPLAN_DB. Teste ce que la fonction rend, pas la façon dont elle le calcule. Ne modifie pas le code de l'application. Mets à jour le nombre de tests dans CLAUDE.md, puis commite les tests et CLAUDE.md.
   ```

   Relisez la liste des comportements que l'agent a figés. Vérifiez que le commit ne touche
   rien sous `src/` (`git show --stat HEAD`).

3. Dans une nouvelle session, faites découper la fonction, un pas par commit, avec le
   périmètre écrit. Un prompt possible :

   ```text
   Découpe unpaid_invoices en fonctions plus petites, sans changer ce qu'elle rend. Une étape à la fois : à chaque étape tu extrais une seule partie, tu lances la suite complète avec PACHAPLAN_DB et ruff, et tu commites si tout est vert. Ne touche qu'à unpaid_invoices et aux fonctions que tu crées : pas de renommage ailleurs, pas de réorganisation du module, pas de changement des requêtes SQL. Si tu vois autre chose à améliorer, note-le dans ta réponse au lieu de le faire. Arrête-toi quand unpaid_invoices fait moins de 40 lignes.
   ```

   Si l'agent modifie un test pour faire passer un pas, refusez : un refactoring ne change
   pas ce que la fonction rend.

4. Rejouez chaque commit vous-même, puis comparez le rapport :

   ```bash
   git rebase --exec 'PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q && uv run ruff check' module-07-end
   uv run pachaplan unpaid --days 30 | diff ../unpaid-avant.txt -
   ```

## Le critère

```bash
bash <(git show origin/course:exercises/module_07/check.sh)
```

Le script affiche une ligne par contrôle, `OK` ou `FAIL`, et sort en code 1 si l'un échoue :

- au moins deux commits depuis `module-07-end` ;
- le premier ajoute ou modifie des tests et ne touche rien sous `src/` ;
- des commits suivants modifient `src/pachaplan/planning.py` ;
- les tests du premier commit passent sur le code de `module-07-end`, et sur votre dernier
  commit ;
- `PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q` passe, sans test sauté ;
- `uv run pachaplan unpaid` avec `--days 10`, `30` et `90` affiche exactement ce qu'il
  affichait à `module-07-end` ;
- `unpaid_invoices` fait moins de 40 lignes ;
- `uv run ruff check` sort en code 0.

Tout est bon quand la dernière ligne est `All checks passed.` Le script lance la suite
plusieurs fois ; comptez une à deux minutes si vos tests sur la vraie base sont lents.

## À réfléchir

- Parmi les comportements que l'agent a figés, lesquels mériteraient un ticket ?
- Vos tests de caractérisation tombent-ils si vous cassez la règle des relances (passez
  `> 60` à `>= 60`, par exemple) ? Essayez, puis `git restore`.
- Qu'aurait-il fallu faire si un pas du découpage avait changé le rapport ?
