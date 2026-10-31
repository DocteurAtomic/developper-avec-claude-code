# Exercice du module 8

Une session a écrit des tests pour le rapport des impayés et les a commités avec un message
qui finit par « All 12 tests pass. » La comptabilité s'apprête à demander une évolution de ce
rapport, et l'équipe veut savoir ce que valent ces douze tests avant de s'appuyer dessus.

Ils ont trois défauts. L'un ne tourne jamais, même avec `PACHAPLAN_DB`. Un autre a une
assertion qui passerait sur une sortie vide. Le troisième teste un cas où le défaut qu'il
devrait voir ne se voit pas. À vous de les trouver, puis de les faire corriger.

## Le départ

Partez de l'étiquette `module-08-end`, et posez dessus le commit de la session :

```bash
git switch -c exercise-08 module-08-end
git show origin/course:exercises/module_08/start.patch | git am
git tag exercise-08-start
uv sync
export PACHAPLAN_TODAY=2026-11-02
```

Le fichier est `tests/test_unpaid_report.py`. Le message du commit est celui de la session :
`git log -1`.

## Les consignes

1. Mesurez avant de lire. Combien de tests le fichier contient-il, combien passent, combien
   sont sautés, avec et sans la variable ? `pytest -rs` affiche la raison de chaque saut.
2. Dans une session `claude`, demandez une étape de cassure pour chaque test du fichier :
   casser le code que le test est censé vérifier, prouver par `grep` que la cassure est en
   place, lancer le test, remettre le code. Un prompt possible :

   ```text
   Une session précédente a écrit tests/test_unpaid_report.py et dit que les 12 tests passent. Je ne la crois pas sur parole. Pour chaque test du fichier, dis-moi s'il tourne vraiment avec PACHAPLAN_DB, si son assertion passerait sur une sortie vide, et s'il tombe quand on casse le code qu'il vérifie : fais la cassure, prouve-la par grep, lance le test, puis remets le code avec git checkout. Ne corrige rien. À la fin, dis-moi ce qui a réussi, ce qui a échoué, et ce que tu n'as pas pu vérifier.
   ```

3. Faites corriger les trois tests sur place, sans les renommer, sans en supprimer, et sans
   toucher au code de l'application (`src/`). Chaque test corrigé doit tomber sur la cassure
   qui le visait.
4. Vérifiez vous-même ce que l'agent affirme : le nombre de tests, zéro sauté, chaque
   cassure. Le critère ci-dessous en refait une partie.

## Le critère

```bash
PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q -rs
```

La dernière ligne est `60 passed`, sans `skipped` (48 tests à `module-08-end`, plus les douze
du fichier). Si vous ajoutez des tests, le nombre augmente d'autant, et vous devez savoir
dire lequel.

Puis le script de l'exercice, qui casse le code trois fois et remet tout en place :

```bash
bash <(git show origin/course:exercises/module_08/check.sh)
```

Il vérifie que `src/` n'a pas bougé depuis `module-08-end`, que la suite passe sans test
sauté et compte au moins 60 tests, que les douze tests du fichier sont toujours là, et que
chacune de ces trois cassures fait tomber au moins un test :

- les factures émises le jour de la date limite disparaissent du rapport
  (`invoice_date <= ` devient `invoice_date < `) ;
- `print_unpaid` n'affiche plus rien ;
- la deuxième relance attend 25 jours au lieu de 15.

Tout est bon quand la dernière ligne est `All checks passed.` Comptez une minute : le test sur
la vraie base prend une quinzaine de secondes, et le script lance la suite quatre fois.

## À réfléchir

- Le test sauté l'aurait-il été dans la CI de `module-08-end` ? Qu'aurait-elle affiché ?
- Le test qui ne tombe pas avait une assertion juste. Qu'est-ce qui lui manquait ?
- Ce que l'agent vous a rendu à l'étape 2 : qu'avez-vous revérifié vous-même, et pourquoi
  cela et pas le reste ?
