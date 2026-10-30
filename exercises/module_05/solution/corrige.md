# Corrigé de l'exercice du module 5

Joué le 30 octobre 2026 avec Claude Code 2.1.314, sur une branche `exercice-05` partie de
`module-05-end`. L'agent écrira autre chose chez vous : le critère se vérifie par les
commandes, pas par comparaison avec ce code.

## L'interview

Plan mode, puis le prompt de l'énoncé. L'agent a lu `planning.py`, la CLI, les tests et la
fixture, interrogé la base en lecture seule, puis posé quatre questions :

| Question | Réponse donnée |
|---|---|
| Le critère : un nombre minimum d'inscrits, un taux de remplissage, ou les deux ? | tapée : taux strictement sous 40 %, inscriptions actives sur les places du cours |
| La fenêtre : une option `--within`, 30 jours comme `sessions`, ou une date limite ? | tapée : du jour de référence à quinze jours plus tard, bornes comprises, sans option |
| Les exclusions : l'intra-entreprise, les sessions `CONFIRMED`, ou aucune ? | « Aucune exclusion » (parmi les sessions actives ; `CANCELED` reste dehors) |
| Les colonnes : celles de `sessions`, le chiffre d'affaires en jeu, le type de formateur... | tapée : `identifiant;date;titre;inscrits;places`, rien d'autre, triées par date puis identifiant |

Puis une seconde série, sur ce que les réponses laissaient ouvert :

| Question | Réponse donnée |
|---|---|
| Le seuil de 40 % : fixe ou en option ? | fixe |
| Rien ne correspond : que sort la commande ? | rien, code 0 |
| Un `;` dans un titre casserait le format (aucun dans la base, vérifié) : que faire ? | le remplacer par une virgule |

L'intra-entreprise est une bonne question, que l'énoncé ne tranchait pas : une session vendue
à un client ne s'annule pas pour un manque d'inscrits. Le service, ici, la veut dans la liste.
Une autre réponse se défendait, mais elle aurait fait échouer le critère : 22 sessions dans la
liste de la requête, intra comprise.

## Le plan

Sept tests dans `tests/test_cancel.py` : la fixture (seule la session 101), les deux bornes de
la fenêtre (le 2 et le 17 novembre dedans, le 1er et le 18 dehors), le seuil strict (4 sur 10
dehors, 3 sur 10 dedans), la liste d'attente et les inscriptions annulées, le tri, le format,
la ligne de commande avec une sortie vide. La fonction réutilise `upcoming_sessions` et
`count_enrollments`. Une ligne dans chaque partie du `README`. Rien à corriger dans ce plan :
il couvrait déjà les bornes et le seuil.

## Le résultat

Après l'approbation, 3 minutes :

```text
PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q : 20 passés, 0 sauté (13 existants + 7 nouveaux).
```

Une remarque de l'agent, utile : les fonctions `print_*` du projet prennent
`out=sys.stdout` comme valeur par défaut, fixée au chargement du module, si bien que `capsys`
ne voit pas ce qu'elles écrivent. Son test de la ligne de commande échouait pour cette raison,
et il a passé `sys.stdout` explicitement. Il a ajouté que le même défaut rend
`tests/test_cli.py::test_cli_sessions_runs_without_error` inutile, sans y toucher. C'est la
matière du module 8. Les tests du service lancent la vraie ligne de commande dans un
processus à part, pour ne pas dépendre de ce détail.

## Le critère

```text
$ git show origin/course:exercises/module_05/test_cancel_candidates.py > tests/test_cancel_candidates.py
$ PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q
.........................                                                [100%]
25 passed in 0.18s
$ diff <(uv run pachaplan cancel-candidates | cut -d';' -f1) <(sqlite3 -readonly data/pachaplan.sqlite "...") && echo IDENTIQUES
IDENTIQUES
$ uv run pachaplan cancel-candidates | head -3
17663;2026-11-02;Azure: the fundamentals;0;12
17669;2026-11-02;SQL Server 2022: high availability and Always On;1;10
17679;2026-11-03;TypeScript: typing your JavaScript code;2;10
$ uv run pachaplan cancel-candidates | wc -l
22
```

Les tests du service voient bien ce qu'ils doivent voir. Sur `module-05-end`, sans la
commande, les cinq échouent. Avec la fenêtre ramenée à 14 jours dans la solution, un seul
échoue, `test_fifteenth_day_is_included_and_sixteenth_is_not`.

## La solution

`cancel-candidates.patch`, à appliquer sur `module-05-end` :

```bash
git apply <chemin du corrigé>/cancel-candidates.patch
```

Il touche `src/pachaplan/planning.py`, `src/pachaplan/cli.py`, `README.md` et ajoute
`tests/test_cancel.py`.
