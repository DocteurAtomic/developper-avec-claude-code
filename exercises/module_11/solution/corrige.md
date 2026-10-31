# Corrigé de l'exercice du module 11

Les deux scripts de ce dossier sont une solution possible parmi d'autres. Le critère est
`check.sh` : deux hooks écrits autrement passent s'ils rendent les mêmes décisions.

## Les fichiers

- `.claude/hooks/no_push.py` : le hook `PreToolUse` sur `Bash`.
- `.claude/hooks/tests_before_stop.py` : le hook `Stop`.
- `settings-hooks.json` : les deux blocs à ajouter sous la clé `hooks` de
  `.claude/settings.json`. Le bloc `PreToolUse` s'ajoute à la liste qui contient déjà le
  hook de `data/` ; `Stop` est une clé nouvelle. Les deux hooks sont lancés par
  `uv run --project ${CLAUDE_PROJECT_DIR} python`, comme ceux du module, ce qui évite de
  dépendre d'un `python3` ou d'un `jq` installés sur la machine.

## Le refus de `git push`

Le script cherche `git`, puis `push` plus loin dans la même commande simple, avant un `;`,
un `&&` ou un `|`. Il attrape `git push`, `git -C . push`, `cd x && git push`,
`git push --force`. Il sort en 2, et sa sortie d'erreur est le message que l'agent lit :

```text
PreToolUse:Bash hook error: [uv run --project ${CLAUDE_PROJECT_DIR} python ${CLAUDE_PROJECT_DIR}/.claude/hooks/no_push.py]: git push is refused in this project: commit, report what you did, and leave the push to the developer after review.
```

Il refuse aussi `git log --grep=push`, à tort : c'est le prix d'une expression régulière.
Une version qui découpe la commande en sous-commandes (une session de mes essais l'a écrite,
avec `shlex`) fait mieux, et reste une approximation : la documentation dit elle-même, du
filtre `if`, que pour un refus qui doit tenir, il y a les permissions. La règle `deny`
`Bash(git push:*)` du module 9 reste donc en place. Le hook ajoute les variantes et la
raison.

## Le hook `Stop`

```python
if event.get("stop_hook_active"):
    return 0
```

`stop_hook_active` est vrai quand l'agent continue déjà à cause d'un hook `Stop`. Le
laisser s'arrêter à ce moment-là évite la boucle sur un test qu'il ne sait pas réparer. La
documentation ajoute un plafond de huit relances consécutives, remis à zéro dès que
l'agent appelle un outil : sans le champ, un agent qui lance les tests à chaque tentative
pourrait donc tourner bien plus longtemps que huit fois.

La suite tourne avec `PACHAPLAN_DB=data/pachaplan.sqlite` et `--fail-on-skip`, comme dans
la CI. Sans la variable, les huit tests d'intégration et de caractérisation sont sautés : un
test d'intégration rouge passerait, et `check.sh` le voit (son test rouge ne tombe qu'avec
la variable). Avec `--fail-on-skip` sans la variable, chaque fin de tour serait bloquée,
suite verte comprise.

Sur une suite rouge, le hook sort en 2 avec les quinze dernières lignes de `pytest` sur la
sortie d'erreur. Une autre solution sort en 0 avec `{"decision": "block", "reason": ...}`
sur la sortie standard : `check.sh` accepte les deux.

## Les mesures

Sur l'état `module-11-end` plus ces deux hooks, avec Claude Code 2.1.314 :

- `bash check.sh push.jsonl` : sept `OK`, `All checks passed.`, en deux secondes environ ;
- hooks non commités, « pousse la branche » : l'agent lit `.claude/settings.json`, refuse
  sans essayer (une fois sur une) ; le dernier contrôle tombe ;
- hooks commités : `git push -u origin exercise-11` essayé deux fois sur deux, message du
  hook reçu, rien de poussé ;
- une suite rendue rouge (la garde d'`export` désactivée) et la demande « Résume en une
  phrase ce que fait ce dépôt » : le hook `Stop` renvoie l'agent, qui trouve la
  modification non commitée et l'explique sans la corriger, puis s'arrête au second
  passage (`stop_hook_active` vrai) ;
- les deux hooks écrits par l'agent avec le prompt de l'énoncé, en auto mode (2 min 11 s) :
  sept `OK` aussi, son hook `Stop` répondant en JSON.
