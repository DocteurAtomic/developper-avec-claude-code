# Corrigé de l'exercice du module 15

Joué le 31 octobre 2026 avec Claude Code 2.1.316, sur `module-15-end`. Deux revues : celle
que l'agent a écrite seul, en `claude -p`, et la mienne, `SECURITY-REVIEW.md` à côté de ce
fichier, écrite après avoir relu la sienne. Vos trouvailles ne seront pas les miennes : le
critère est `check.sh` et la grille de l'énoncé.

## La revue de l'agent

Le prompt, en mode `acceptEdits`, avec le modèle déjà copié à la racine :

```text
Deux développeurs arrivent lundi. Avant de leur confier le dépôt, fais la revue de sécurité de la configuration Claude Code du projet, dans SECURITY-REVIEW.md, en suivant le modèle qui s'y trouve : .claude/settings.json (règles, hooks, bac à sable), .claude/hooks/, .mcp.json et son serveur, le skill relances, le sous-agent doc-checker, scripts/monday-note.sh, .github/workflows/claude-review.yml, .gitignore, et ce qui reste sur le poste de chacun. Pour chaque trouvaille : la jambe (données privées, contenu non fiable, sortie, exécution), ce qui la tient (mécanique, consigne, rien), et une décision (avant de partager, accepté, plus tard). Ne modifie rien d'autre que SECURITY-REVIEW.md : je déciderai des changements.
```

Vingt-six trouvailles, dans les sept sections, en 24 tours, cinq minutes et 1,28 $. Il a lu chaque fichier, et il a vérifié
certaines choses depuis le bac à sable, avec `os.access`, sans ouvrir les fichiers.

Ce qu'il a trouvé et que je n'avais pas :

- La plus grave de la revue. Une commande du bac à sable peut écrire dans `.venv`, et un
  fichier `.pth` posé dans `site-packages` s'exécute au démarrage de ce Python, donc dans
  les hooks et dans le serveur MCP, qui tournent dehors. Je l'ai vérifié : un fichier
  témoin, écrit par ce `.pth` dans un dossier où le bac à sable ne peut pas écrire, est
  apparu après une seule édition, six lignes, une par démarrage de Python (le serveur MCP,
  `protect_data.py`, `ruff_after_edit.py`, deux fois chacun). La documentation protège les
  fichiers des hooks eux-mêmes (`.claude/hooks`), pas ce qu'ils exécutent.
- Les secrets du répertoire personnel, lisibles depuis le bac à sable. La documentation le
  dit (« Default read behavior: read access to the entire computer »), et je ne l'avais
  pas relié à la revue.
- Les exports CSV (`pachaplan export -o`, `relances.py -o`) et les copies de travail en `*.sqlite` qu'aucun
  `.gitignore` ne couvre. Je l'ai laissé dans sa revue, pas dans la mienne.

Ce qu'il a manqué, et que `check.sh` signale : les hooks et `.mcp.json` qui tournent en
`claude -p` dans un dossier jamais approuvé, et le repli sans `bubblewrap`. Les deux ne se
lisent dans aucun fichier du dépôt : il faut les avoir mesurés (vidéos 15.2 et 15.4).

Ce que je n'ai pas repris :

- « La base réelle est dans le dépôt », marqué avant de partager. `data/pachaplan.sqlite`
  est une base de démonstration, versionnée exprès ; et le changement qu'il propose
  casserait le critère « projet intact ».
- Plusieurs « Tenu par » nuancés (« mécanique pour les deux outils actuels… »). C'est
  juste, et `check.sh` l'accepte, mais une revue se lit mieux quand le premier mot
  tranche.
- Il n'a rien modifié d'autre que la revue, comme demandé. Les quatre changements qu'il
  marque avant de partager restent à faire : c'est ce que le quatrième contrôle refuse.

## Mes changements

Dans `exercise-15.patch`, sur `.claude/settings.json`, `.gitignore` et `CLAUDE.md` :

- les deux outils MCP par leur nom, au lieu de `mcp__pachaplan__*`, et la ligne du
  `CLAUDE.md` qui le dit ;
- `Read(./.env.*)` et `Read(!.env.example)` dans les refus, `.env.*` et `!.env.example`
  dans le `.gitignore` ;
- `.claude/settings.local.json` dans le `.gitignore` du projet ;
- `"disableBypassPermissionsMode": "disable"` ;
- `"denyWrite": ["./.venv"]` dans le bac à sable ;
- `sandbox.credentials` pour `~/.ssh`, `~/.git-credentials` et
  `~/.claude/.credentials.json`.

Vérifié après coup, chacun dans une session `claude -p` : `.env.local` refusé par le bac à
sable (`PermissionError`), `.env.example` toujours lisible ; 36 sessions par l'outil MCP
nommé ; 75 tests passés et `ruff` propre avec `.venv` en lecture seule, et `touch
.venv/zz-probe` refusé ; `ls ~/.ssh` vide et le fichier d'identifiants refusé. Le prix du
refus sur `.venv` : `uv sync` et `uv add` ne passent plus dans le bac à sable, on les lance
soi-même, avec `!` ou dans un autre terminal.

## Les points ouverts

- `src/` s'écrit depuis le bac à sable, et le serveur MCP exécute ce code au démarrage de
  la session suivante. C'est le métier de l'agent d'écrire dans `src/` ; ce qui le
  retient, c'est le `git diff` relu avant de relancer une session.
- `claude-review.yml` : l'effet du bac à sable du dépôt sur le runner GitHub n'est pas
  vérifié.
- L'auto mode laisse le classifieur décider des hôtes. `strictAllowlist` se règle chez
  chacun, pas dans le dépôt.
