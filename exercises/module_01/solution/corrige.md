# Corrigé du module 1

Joué le 30 octobre 2026 avec Claude Code 2.1.314, Opus 5.5, dans une session interactive en
auto mode, `PACHAPLAN_TODAY=2026-11-02`. Les réponses de l'agent varient d'une session à
l'autre ; les commandes de vérification rendent la même sortie.

## La grille

| Question | Réponse de l'agent | Commande de vérification | Ce qu'elle rend | Confirmée ou réfutée |
|---|---|---|---|---|
| 1 | `course.max_attendees` pour la capacité, les lignes de `enrollment` sans `cancellation_date` et hors liste d'attente pour les inscrits | `grep -n "max_attendees\|waiting_list" src/pachaplan/planning.py` | `waiting_list` ligne 121 (`count_enrollments`), `max_attendees` lignes 132 et 150 (`low_fill_sessions`) | confirmée, numéros de ligne faux d'une unité |
| 2 | 867 factures, solde 2 424 631,24 | `uv run pachaplan unpaid --days 30 \| grep "unpaid invoice"` | `867 unpaid invoice(s) issued 30 days ago or more (on or before 2026-10-03)` | confirmée |
| 3 | Brian Prokopowicz, `trainer_id` 49 | la requête `sqlite3 -readonly` de l'énoncé | `Brian\|Prokopowicz` | confirmée |

## Question 1

L'agent a lancé trois commandes (un `grep` sur le dépôt, `sed -n 115,170p` sur
`planning.py`, le schéma de trois tables), puis répondu juste, en ajoutant que `room.seats`
existe mais ne sert pas au calcul. Il a situé `low_fill_sessions` à la ligne 144 et
`count_enrollments` à la ligne 115 :

```text
$ grep -n "^def count_enrollments\|^def low_fill_sessions\|rate = " src/pachaplan/planning.py
116:def count_enrollments(conn, session_id):
145:def low_fill_sessions(conn, today, below):
151:        rate = 100.0 * enrolled / capacity if capacity else 0.0
```

Il avait lu le fichier par `sed`, sans numéros de ligne, et les a déduits. La réponse est
juste ; ses références, à une ligne près. Après sa réponse, la zone de saisie proposait en
grisé « utilise room.seats comme capacité plutôt que max_attendees » : c'est une suggestion de
prompt, que `Tab` aurait acceptée, et pas une demande du service.

## Question 2

Il a lancé `uv run pachaplan --today 2026-11-02 unpaid --days 30`, avec la date de la
question, et répondu 867. La commande de l'énoncé rend la même ligne. Sans `PACHAPLAN_TODAY`,
la date est celle de la machine ; le 30 octobre 2026 :

```text
$ uv run pachaplan unpaid --days 30 | grep "unpaid invoice"
760 unpaid invoice(s) issued 30 days ago or more (on or before 2026-09-30), balance 2 058 994.75.
```

Si votre grille montre un autre nombre que 867, regardez d'abord la date entre parenthèses.

## Question 3

Deux requêtes `sqlite3 -readonly`. Il a ajouté que la session commence le 2026-11-16 et dure
quatre jours. Le même formateur a la session 17735 le 18 novembre : le chevauchement, que
`pachaplan trainers` ne signale pas, est la matière du module 7.

```text
$ sqlite3 -readonly data/pachaplan.sqlite "SELECT session_id, start_date, duration_days, trainer_id FROM session WHERE session_id IN (17709, 17735);"
17709|2026-11-16|4|49
17735|2026-11-18|2|49
```

## Par `claude -p`

Posée par `claude -p`, sans `--allowedTools`, la question 2 démarre en Manual : trois
commandes refusées (`uv run pachaplan --today 2026-11-02 unpaid --days 30`, deux fois, puis
une requête `sqlite3 -readonly`). L'agent n'a pas donné de nombre : « Je n'ai pas le nombre :
les deux commandes qui permettaient de l'obtenir attendent votre approbation, donc je n'ai
rien exécuté. » Il a proposé les commandes à lancer soi-même et décrit le calcul d'après le
code. Le module 4 montre comment lui autoriser une seule commande.
