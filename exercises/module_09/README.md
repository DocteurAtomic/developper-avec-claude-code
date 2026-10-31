# Exercice du module 9

Les douze tests du rapport des impayés, ceux de l'exercice du module 8, reviennent avant
leur correction. L'équipe veut un relecteur de tests qu'elle puisse relancer à chaque
nouveau fichier de tests : un sous-agent du projet, `test-reviewer`, qui lit et ne modifie
rien. Vous l'écrivez, vous le lancez sur ces douze tests, puis vous confrontez son rapport
aux trois défauts connus.

## Le départ

Partez de l'étiquette `module-09-end`, et posez dessus le commit de la session du module 8 :

```bash
git switch -c exercise-09 module-09-end
git show origin/course:exercises/module_08/start.patch | git am
git tag exercise-09-start
uv sync
export PACHAPLAN_TODAY=2026-11-02
```

Vous n'avez pas besoin d'avoir fait l'exercice du module 8 : le commit de départ est le même.
Avec la base, `PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q` donne `63 passed,
1 skipped`.

## Les consignes

1. Faites créer le sous-agent par Claude, ou écrivez-le vous-même, dans
   `.claude/agents/test-reviewer.md`. Le frontmatter contient `name: test-reviewer`, une
   `description` qui dit quand déléguer, et `tools: Read, Grep, Glob`. Sans liste `tools`, il
   hérite de tous les outils, `Edit` et `Write` compris. Pour chaque test, son prompt
   lui fait dire s'il tourne vraiment, si son assertion passerait sur une sortie vide, et si
   son cas est près de la limite qu'il garde. Un prompt possible, dans une session
   interactive :

   ```text
   Crée un sous-agent du projet, test-reviewer, dans .claude/agents/. Son travail : relire des tests pytest et dire, pour chaque test, s'il tourne vraiment, si son assertion passerait sur une sortie vide, et si son cas est assez près de la limite qu'il doit garder. Il rend un verdict par test, avec le fichier, la ligne et la preuve. Il ne modifie aucun fichier et ne lance rien : seulement Read, Grep et Glob. Ne commite pas.
   ```

   `.claude/` est un chemin protégé. En mode `acceptEdits`, l'écriture du fichier y demande
   une confirmation, et sous `claude -p` elle est refusée. Créez-le en session interactive, ou
   par `claude -p "..." --permission-mode auto`.

2. Si le dossier `.claude/agents/` n'existait pas au démarrage de la session, Claude Code ne
   le surveille pas : quittez et relancez `claude` avant de lancer le sous-agent.
3. Lancez le sous-agent par `claude -p`, en gardant la trace de l'exécution :

   ```bash
   claude -p "Utilise le sous-agent test-reviewer sur tests/test_unpaid_report.py." \
       --output-format stream-json --verbose < /dev/null > review.jsonl
   ```

   Comptez deux minutes.
4. Confrontez le rapport aux trois défauts, dans une grille :

   | Défaut | Trouvé ? | Ligne citée | Preuve donnée |
   |---|---|---|---|
   | un test qui ne tourne jamais, même avec `PACHAPLAN_DB` | | | |
   | une assertion qui passerait sur une sortie vide | | | |
   | un cas trop loin de la limite qu'il garde | | | |

   Ajoutez une ligne par constat du rapport qui n'est pas l'un des trois, et dites s'il est
   vrai.

Ne corrigez pas les tests : c'était l'exercice du module 8.

## Le critère

```bash
bash <(git show origin/course:exercises/module_09/check.sh) review.jsonl
```

Huit contrôles, tous `OK`, et la dernière ligne `All checks passed.` : le fichier du
sous-agent existe, avec `name: test-reviewer`, une description et des outils limités à
`Read`, `Grep` et `Glob` ; la trace montre un appel à l'outil `Agent` avec `subagent_type`
`test-reviewer` ; le sous-agent n'a utilisé que ces trois outils ; aucun `Edit` ni `Write`
dans l'exécution ; `src/` et `tests/` n'ont pas bougé depuis `exercise-09-start`.

Le script ne lit pas le rapport : la grille de l'étape 4 est la seconde moitié du critère.

## À réfléchir

- Le sous-agent ne peut rien lancer. Lesquels de ses verdicts sont des lectures, et lequel
  l'agent principal a-t-il vérifié par une commande ?
- Sa `description` décide quand l'agent principal lui délègue. Qu'y avez-vous mis, et
  l'agent principal l'a-t-il choisi seul, sans que vous le nommiez ?
- Une consigne « ne modifie rien » dans le corps du fichier et une liste `tools` sans `Edit`
  ni `Write` : laquelle des deux est une barrière ?
