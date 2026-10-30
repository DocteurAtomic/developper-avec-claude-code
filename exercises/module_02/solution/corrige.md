# Corrigé de l'exercice du module 2

Le fichier de référence, `solution/settings.json` :

```json
{
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Bash(uv run pytest:*)",
      "Bash(uv run ruff:*)"
    ],
    "deny": [
      "Bash(git push:*)",
      "Read(./.env)",
      "Edit(./data/**)",
      "Bash(rm:*)"
    ]
  }
}
```

L'ordre des règles dans une liste n'a pas d'importance. Ce qui compte, c'est la liste où
elles sont : `deny`, puis `ask`, puis `allow`.

## Les règles, une par une

- `Bash(uv run ruff:*)` autorise `uv run ruff check`, `uv run ruff format`, et rien d'autre
  sous `uv run`. La règle que propose la question de permission, `uv run *`, autoriserait
  aussi `uv run python -c ...`, donc n'importe quel programme.
- `Edit(./data/**)` couvre tous les outils qui écrivent un fichier, `Write` compris, et les
  redirections de Bash comme `> data/note.txt`. Une règle `Write(./data/**)` est acceptée
  sans message et ne correspond jamais : dans mes répétitions, l'écriture dans
  `data/note.txt` passait avec elle.
- `Bash(rm:*)` : en `acceptEdits`, Claude Code approuve seul `rm` et `rmdir` dans le dossier
  de travail. Sans cette règle, `supprime le fichier tmp/note.txt` supprime le fichier sans
  question. Avec elle, la commande est refusée.
- `"defaultMode": "acceptEdits"` vaut depuis le fichier du projet. Les valeurs `auto` et
  `bypassPermissions` n'y prennent pas effet : un dépôt cloné ne peut pas choisir pour vous
  un mode qui retire les questions. Elles se posent dans vos réglages utilisateur, ou par
  `--permission-mode` pour une session.

## Ce que vérifie chaque épreuve

| Épreuve | Ce qu'elle vérifie |
|---|---|
| `ruff`, sortie d'erreur sans « not been trusted » | la règle `allow` est appliquée, donc le dossier est approuvé |
| `tmp/note.txt` écrit | le mode `acceptEdits` est actif ; en Manual, l'écriture serait refusée |
| `data/note.txt` refusé | la règle `Edit(./data/**)` ; sans l'épreuve précédente, le refus pourrait venir du mode Manual |
| `tmp/note.txt` toujours là après `supprime` | la règle `Bash(rm:*)` |
| empreinte de la base | rien n'a écrit dans `data/pachaplan.sqlite` |

## Les questions

- Sans `defaultMode`, `claude -p` démarre en Manual : toute écriture demande une approbation,
  et personne n'est là pour la donner. Le refus dans `data/` ne prouvait rien. L'écriture dans
  `tmp/` montre que les écritures passent ailleurs, donc que le refus dans `data/` vient bien
  de la règle.
- Le mode `acceptEdits` approuve `rm` dans le dossier de travail. Une règle `deny` est le seul
  moyen de garder la suppression hors de ce que l'agent fait seul.
- Un `defaultMode` à `auto` ou `bypassPermissions` dans un dépôt donnerait à n'importe quel
  projet cloné le pouvoir de supprimer vos questions. Claude Code ne les accepte que de vos
  propres réglages (`permission-modes.md`, « Which mode a session starts in »).
- Par un programme qui ouvre le fichier lui-même, un script Python par exemple : les règles
  `Edit` et `Read` ne le voient pas. En Manual ou en `acceptEdits`, la commande `python3`
  demanderait une approbation. En auto mode, le classifieur en jugerait. La protection qui ne
  dépend pas du texte de la commande, c'est le bac à sable (module 15). Pour la base,
  `pachaplan` l'ouvre de toute façon en lecture seule.
