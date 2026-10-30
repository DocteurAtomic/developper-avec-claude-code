# Corrigé du module 4

Joué le 30 octobre 2026 avec Claude Code 2.1.314, Opus 5.5. Les réponses de l'agent varient
d'une session à l'autre ; les commandes de vérification rendent la même sortie.

## Tâche 1

Sans autorisation, en Manual, l'agent a essayé `uv run pachaplan --help`, une requête
`sqlite3 -readonly` et un script Python : tout a été refusé. Il n'a pas donné de nombre, et
a proposé la requête à lancer soi-même.

Avec la commande autorisée :

```bash
claude -p "combien de sessions commencent en novembre 2026 ?" \
  --allowedTools "Bash(sqlite3 -readonly data/pachaplan.sqlite:*)"
```

Réponse : 123 sessions, dont 96 `CONFIRMED` et 27 `OPEN`, en 5 tours. La requête de
l'énoncé rend 123.

`-readonly` fait partie de la règle : la règle n'autorise que les commandes qui commencent
par ce texte. Un `sqlite3 data/pachaplan.sqlite "UPDATE ..."` resterait refusé.

## Tâche 2

Dans ma répétition, l'agent a ajouté la colonne `country` au rapport `unpaid`, un test dans
`tests/test_unpaid.py` et une ligne dans `CLAUDE.md`, les trois par des scripts lancés par
Bash. Il a aussi lancé de lui-même `uv run pachaplan --today 2026-10-30 unpaid --days 30`,
avec la date du système et non celle du cours.

Le menu de `/rewind` annonçait « No code changes » sous le prompt, et ne proposait que
« Restore conversation ». Après la restauration :

```text
$ git status --porcelain
 M CLAUDE.md
 M src/pachaplan/planning.py
 M tests/test_unpaid.py
$ git restore .
$ git status --porcelain
$
```

`/rewind` ne suit que les fichiers écrits par les outils d'édition de l'agent, et les
modifications que Bash fait ensuite à ces fichiers. Un fichier que seul Bash a touché reste
modifié. Selon la session, l'agent peut aussi passer par ses outils d'édition, et le menu
restaure alors le code : le critère est le même dans les deux cas.

## Tâche 3

```text
$ git log --oneline | claude -p "résume ce journal en deux phrases pour le service planification"
Le projet pachaplan a d'abord été importé dans le dépôt. On a ensuite autorisé l'assistant à
lancer les tests tout en lui interdisant l'accès au fichier `.env` et à `git push`, puis ajouté
un fichier `CLAUDE.md` qui donne la commande à utiliser pour lancer tous les tests.
```

Un tour, aucun outil. Le journal arrive sur l'entrée standard, avec le prompt : l'agent le lit
sans lancer d'outil, et il n'y a pas de permission à donner. Sur `module-04-end`, le journal a un commit de plus et
le résumé parlera aussi de la colonne.
