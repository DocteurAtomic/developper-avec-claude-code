# Exercice du module 11

Le module a posé deux hooks : `ruff` après chaque modification, et le refus de `data/`.
L'équipe en veut deux autres. Que l'agent ne pousse jamais lui-même, quelle que soit la
façon d'écrire la commande. Et qu'il ne vous rende pas la main sur une suite de tests
rouge, tout en pouvant s'arrêter quand il n'arrive pas à la réparer.

## Le départ

Partez de l'étiquette `module-11-end`, la fin du module :

```bash
git switch -c exercise-11 module-11-end
uv sync
export PACHAPLAN_TODAY=2026-11-02
```

## La demande

Deux hooks du projet, déclarés dans `.claude/settings.json`, scripts dans `.claude/hooks/` :

- un hook `PreToolUse` sur `Bash` qui refuse `git push`, y compris `git -C . push` ou
  `cd x && git push`, avec un message qui dit pourquoi et quoi faire à la place ;
- un hook `Stop` qui lance la suite comme la CI la lance,
  `PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q --fail-on-skip`, et renvoie l'agent
  au travail tant qu'elle échoue, sauf quand le champ `stop_hook_active` de son entrée
  JSON est vrai.

Gardez les règles et les hooks qui y sont déjà.

## Les consignes

1. Faites écrire les hooks par Claude, ou écrivez-les vous-même. Un prompt possible, en
   session interactive (en auto mode, dans mes essais, l'agent a pu écrire dans
   `.claude/`) :

   ```text
   Ajoute deux hooks au projet, scripts dans .claude/hooks/, déclaration dans .claude/settings.json sans toucher au reste. Un hook PreToolUse sur Bash qui refuse git push, quelles que soient les options avant push, avec un message qui dit pourquoi. Un hook Stop qui lance la suite comme la CI, PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q --fail-on-skip, et te renvoie au travail tant qu'elle échoue, sauf quand stop_hook_active est vrai. Ne commite pas.
   ```

   Sous `claude -p --permission-mode acceptEdits`, l'écriture sous `.claude/` est refusée.

2. La variable. Sans `PACHAPLAN_DB`, huit tests sont sautés et la suite sort en 0 : un hook
   `Stop` qui lance `uv run pytest -q` tout court laisse passer une suite dont les tests
   d'intégration sont rouges. Avec `--fail-on-skip` mais sans la variable, il bloque au
   contraire chaque fin de tour. Le hook définit donc la variable lui-même.
3. Le code de sortie. Pour bloquer, le hook sort en 2 (la sortie d'erreur est le message
   que lit l'agent), ou sort en 0 avec `{"decision": "block", "reason": "..."}` sur sa
   sortie standard. Un code 1 ne bloque rien.
4. Essayez les deux hooks à la main, en leur passant un JSON sur l'entrée standard, comme
   le fait Claude Code. Par exemple :

   ```bash
   echo '{"tool_name":"Bash","tool_input":{"command":"git -C . push origin HEAD"}}' \
     | uv run python .claude/hooks/<votre-script>.py; echo $?
   echo '{"hook_event_name":"Stop","stop_hook_active":true}' \
     | uv run python .claude/hooks/<votre-script>.py; echo $?
   ```

5. Commitez les deux hooks. Dans mes essais, avec des hooks pas encore commités, l'agent a
   refusé de pousser sans même essayer ; une fois commités, il a essayé deux fois sur deux,
   et le hook l'a arrêté.
6. Demandez-lui de pousser, dans une session neuve, en gardant la trace :

   ```bash
   claude -p "pousse la branche" --output-format stream-json --verbose \
       < /dev/null > push.jsonl
   ```

   S'il refuse sans essayer, demandez-le explicitement :

   ```bash
   claude -p "Essaie de pousser la branche avec git push origin exercise-11, et rapporte exactement ce que l'outil te répond." \
       --output-format stream-json --verbose < /dev/null > push.jsonl
   ```

   Rien ne part : la règle `deny` `Bash(git push:*)`, posée au module 9, est toujours là.
   Dans mes essais, c'est le message du hook qui arrive, parce qu'un hook qui sort en 2
   passe avant les règles de permission.

## Le critère

```bash
bash <(git show origin/course:exercises/module_11/check.sh) push.jsonl
```

Sept contrôles, tous `OK`, et la dernière ligne `All checks passed.` : la suite est verte
avec la variable et `--fail-on-skip` ; le hook `Stop` laisse s'arrêter sur une suite verte ;
il renvoie au travail sur une suite rouge quand `stop_hook_active` est faux, et laisse
s'arrêter quand il est vrai ; le hook `PreToolUse` refuse `git -C . push origin HEAD` et
laisse passer `git status --short` ; la session a essayé `git push` et reçu le message du
hook (`PreToolUse:Bash hook error`).

Le script lit vos hooks dans `.claude/settings.json` et les lance comme Claude Code, avec un
JSON sur l'entrée standard. La suite rouge est un test temporaire,
`tests/test_zz_check_red.py`, qui ne tombe qu'avec `PACHAPLAN_DB`, comme les tests
d'intégration ; il est retiré à la sortie du script. Le script ne lance pas `claude` et ne
pousse rien. Il ne compare pas vos scripts au corrigé : deux hooks différents passent s'ils
rendent les mêmes décisions.

## À réfléchir

- La règle `deny` `Bash(git push:*)` refusait déjà le push. Qu'ajoute le hook ? Lequel des
  deux tiendrait si l'agent écrivait la commande d'une façon que ni la règle ni votre
  expression régulière n'ont prévue ?
- Sans `stop_hook_active`, que se passerait-il sur un test que l'agent ne sait pas
  réparer ? La documentation prévoit un plafond de huit relances consécutives : à quoi
  servirait encore le champ ?
- Votre hook `Stop` lance toute la suite à chaque fin de tour. Combien de temps prend-elle
  ici, et à partir de quelle durée le feriez-vous autrement ?
