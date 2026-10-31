# Revue de sécurité de la configuration Claude Code de pachaplan

Relue sur `module-15-end`, le 31 octobre 2026, avec Claude Code 2.1.316. Corrigé de
l'exercice du module 15 : une revue parmi d'autres possibles.

## Permissions

### La règle `Bash(git push:*)`
- Fichier : `.claude/settings.json`
- Permet : `git -C . push`, `git -c push.default=current push` ou `sh -c 'git push'` ne correspondent pas à la règle `Bash(git push:*)`, qui compare le texte écrit.
- Jambe : sortie
- Tenu par : consigne
- Décision : accepté
- Changement : rien dans la règle, qui arrête la forme que l'agent écrit d'habitude. Ce qui tient vraiment, c'est le bac à sable (le push passe par le réseau, hôte par hôte) et la protection de branche sur le dépôt distant. Source : `permissions.md`, « What a Bash rule doesn't match ».

### Le joker `mcp__pachaplan__*`
- Fichier : `.claude/settings.json`
- Permet : tout outil ajouté plus tard au serveur, y compris un outil qui écrirait, est appelé sans question dès qu'il existe.
- Jambe : exécution, sortie
- Tenu par : rien
- Décision : avant de partager
- Changement : les deux outils nommés, `mcp__pachaplan__sessions_starting_in_week` et `mcp__pachaplan__trainer_month_load`. Un outil neuf demandera une règle, donc une relecture. Ligne correspondante du `CLAUDE.md` mise à jour.

### `uv run pytest` autorisé
- Fichier : `.claude/settings.json`
- Permet : `Bash(uv run pytest:*)` lance n'importe quel fichier de test ou `conftest.py` que l'agent vient d'écrire, donc n'importe quel code Python.
- Jambe : exécution
- Tenu par : mécanique
- Décision : accepté
- Changement : rien. Lancer les tests est le métier de l'agent ; depuis `module-15-end`, ce code tourne dans le bac à sable.

### Le mode `bypassPermissions` permis
- Fichier : `.claude/settings.json`
- Permet : un développeur de l'équipe peut lancer `claude --dangerously-skip-permissions` dans ce dépôt, et toutes les règles tombent.
- Jambe : exécution, sortie
- Tenu par : rien
- Décision : avant de partager
- Changement : `"disableBypassPermissionsMode": "disable"` dans `permissions`. La clé vaut depuis n'importe quel fichier (`permissions.md`, « Managed settings »).

## Bac à sable

### Le poste sans bac à sable
- Fichier : `.claude/settings.json`
- Permet : sans `bubblewrap` (Linux, WSL2) ou sous Windows natif, les commandes tournent sans bac à sable. En `claude -p`, un avertissement sort sur stderr ; en session, rien sur l'écran d'accueil (mesuré au module 15, `bwrap` masqué).
- Jambe : sortie, exécution
- Tenu par : rien
- Décision : plus tard
- Changement : pas de `failIfUnavailable` dans le dépôt, il empêcherait Claude Code de démarrer sous Windows natif. Chacun vérifie une fois `/sandbox` (onglet Mode, pas d'onglet Dependencies seul), et ceux qui sont sous Linux ou macOS peuvent mettre `failIfUnavailable` dans leur `~/.claude/settings.json`.

### Les hôtes en auto mode
- Fichier : `.claude/settings.json`
- Permet : un `curl` vers un hôte qui n'est pas dans la liste passe par le proxy, et en auto mode c'est le classifieur qui l'accepte ou le refuse (`example.com` accepté au module 15, sur demande explicite).
- Jambe : sortie
- Tenu par : consigne
- Décision : plus tard
- Changement : `strictAllowlist` ne se règle pas depuis le dépôt. Qui veut un refus sans appel le met dans son `~/.claude/settings.json` ; une entreprise le met dans ses réglages gérés (`allowManagedDomainsOnly`).

### Le cache de uv en écriture
- Fichier : `.claude/settings.json`
- Permet : `filesystem.allowWrite` sur `~/.cache/uv` laisse une commande du bac à sable écrire dans un cache partagé par tous les projets Python du poste.
- Jambe : exécution
- Tenu par : mécanique
- Décision : accepté
- Changement : rien pour l'instant, sans lui aucun `uv run` ne marche dans le bac à sable. À revoir si l'équipe veut un cache par projet (`UV_CACHE_DIR`).

### `.venv` écrit depuis le bac à sable
- Fichier : `.claude/settings.json`
- Permet : une commande du bac à sable peut écrire dans `.venv/lib/python3.13/site-packages/`. Un fichier `.pth` qui y est posé s'exécute à chaque démarrage de ce Python, donc dans les deux hooks (`uv run --project … python`) et dans le serveur MCP, qui tournent hors du bac à sable. Mesuré au module 15 : le fichier témoin, écrit hors du dossier où le bac à sable peut écrire, est apparu six fois après une seule édition (serveur MCP au démarrage, `protect_data.py`, `ruff_after_edit.py`).
- Jambe : exécution, sortie
- Tenu par : rien
- Décision : avant de partager
- Changement : `"denyWrite": ["./.venv"]` dans `sandbox.filesystem`. Les tests et `ruff` passent toujours dans le bac à sable ; `uv sync` ou `uv add` se lancent alors vous-même. Reste ouvert : `src/` s'écrit depuis le bac à sable, et le serveur MCP exécute ce code au démarrage de la session suivante. Le `git diff` le montre avant.

### Les secrets du répertoire personnel
- Fichier : `.claude/settings.json`
- Permet : par défaut, une commande du bac à sable lit tout le disque, sauf ce qui est refusé : `~/.ssh`, `~/.git-credentials`, le fichier d'identifiants de Claude Code (`sandboxing.md`, « Default read behavior »). Seule la sortie réseau les retient, et en auto mode c'est le classifieur qui en décide.
- Jambe : données privées
- Tenu par : rien
- Décision : avant de partager
- Changement : `sandbox.credentials` avec `~/.ssh`, `~/.git-credentials` et `~/.claude/.credentials.json` en `deny`. Mesuré : `ls ~/.ssh` rend une liste vide, la lecture des identifiants « Permission non accordée ». Chacun ajoute ses propres secrets (`~/.aws`, `~/.config/gh`) dans son `~/.claude/settings.json` : une entrée `deny` s'ajoute depuis n'importe quel niveau.

## Hooks

### Les hooks du dépôt
- Fichier : `.claude/hooks/protect_data.py`
- Permet : un hook modifié dans une branche tourne avec tous les droits de l'utilisateur. En `claude -p`, dans un clone jamais approuvé, un hook `SessionStart` du dépôt a tourné (mesuré au module 15) ; `--setting-sources user` l'en empêche.
- Jambe : exécution
- Tenu par : rien
- Décision : accepté
- Changement : rien dans le dépôt. Les hooks se relisent dans les revues comme du code, et un clone neuf s'ouvre d'abord en session, en lisant `.claude/` avant de répondre à la question de confiance, qui ne liste que les règles `allow`.

## Serveur MCP

### `.mcp.json` en `claude -p`
- Fichier : `.mcp.json`
- Permet : en `claude -p`, le serveur déclaré dans `.mcp.json` démarre sans être approuvé, même si le dossier n'a jamais reçu la confiance (mesuré aux modules 13 et 15). La commande du serveur est un programme comme un autre.
- Jambe : exécution
- Tenu par : rien
- Décision : accepté
- Changement : rien, le serveur est le nôtre. Une modification de `.mcp.json` se relit comme un changement de code ; pour un script qui n'en a pas besoin, `--strict-mcp-config`.

### Les remarques des sessions
- Fichier : `src/pachaplan/mcp_server.py`
- Permet : l'outil de la semaine renvoie le champ `remarks`, tapé par n'importe qui dans un formulaire.
- Jambe : contenu non fiable
- Tenu par : mécanique
- Décision : accepté
- Changement : rien : le serveur ne sait pas écrire (`open_read_only`), le `CLAUDE.md` demande de signaler une consigne trouvée dans les données, et depuis `module-15-end` la sortie réseau est tenue par le bac à sable.

## Skill et sous-agent

### Bash dans le sous-agent « en lecture seule »
- Fichier : `.claude/agents/doc-checker.md`
- Permet : `tools: Read, Grep, Glob, Bash`. Sa lecture seule n'est écrite que dans sa prose (« do not work around that with Bash »).
- Jambe : exécution
- Tenu par : consigne
- Décision : plus tard
- Changement : le bac à sable borne déjà ses écritures au dépôt. Plus tard, un hook `PreToolUse` propre au sous-agent, ou une liste d'outils sans Bash si la vérification des commandes peut passer par un script.

### Le `allowed-tools` du skill des relances
- Fichier : `.claude/skills/relances/SKILL.md`
- Permet : `allowed-tools` autorise `uv run python ${CLAUDE_SKILL_DIR}/scripts/relances.py *`, et la confiance du dossier ne s'applique jamais à cette ligne (`permissions.md`, « What runs before you trust a folder »).
- Jambe : exécution
- Tenu par : mécanique
- Décision : accepté
- Changement : rien, la règle est étroite et le script lit seulement. Une modification du skill se relit comme du code.

## Automatisation

### Le jeton de la revue des pull requests
- Fichier : `.github/workflows/claude-review.yml`
- Permet : sur une pull request d'une branche du dépôt, le job tourne avec `CLAUDE_CODE_OAUTH_TOKEN` dans l'environnement, sur le code de la branche, hooks et `.mcp.json` compris.
- Jambe : données privées, exécution
- Tenu par : mécanique
- Décision : accepté
- Changement : rien. Une pull request venue d'un fork ne reçoit pas le secret (le job s'arrête sur la garde), et quelqu'un qui peut pousser une branche dans le dépôt peut déjà modifier le workflow lui-même. Les droits du job sont `contents: read` et `pull-requests: read`, et `persist-credentials: false` garde le jeton GitHub hors de `.git/config`. Non vérifié sur GitHub : l'effet du bac à sable du dépôt sur le runner.

### La note du lundi
- Fichier : `scripts/monday-note.sh`
- Permet : le cron lance `claude -p` dans le dépôt : ses hooks, son serveur MCP et ses règles s'appliquent sur la machine du cron.
- Jambe : exécution
- Tenu par : mécanique
- Décision : accepté
- Changement : rien. Le script est déjà en `dontAsk` avec trois outils nommés, et il vérifie la note au lieu de croire le code de sortie.

## Le poste et le dépôt

### `.claude/settings.local.json` hors du `.gitignore` du projet
- Fichier : `.gitignore`
- Permet : le fichier local (mode du bac à sable, approbation du serveur MCP) n'est ignoré que par le `.gitignore` global, que Claude Code complète lui-même quand il écrit ce fichier (mesuré : `**/.claude/settings.local.json` ajouté à `$XDG_CONFIG_HOME/git/ignore`). Un fichier écrit à la main peut partir dans un commit.
- Jambe : données privées
- Tenu par : rien
- Décision : avant de partager
- Changement : `.claude/settings.local.json` ajouté au `.gitignore` du projet.

### `.env.local` sans protection
- Fichier : `.gitignore`
- Permet : `Read(./.env)` et le `.gitignore` ne visent que `.env`. Un `.env.local` se lit (`python3 -c "print(open('.env.local').read())"` a rendu son contenu dans le bac à sable) et se commite.
- Jambe : données privées
- Tenu par : rien
- Décision : avant de partager
- Changement : `.env.*` et `!.env.example` dans le `.gitignore` ; `Read(./.env.*)` puis `Read(!.env.example)` dans les refus de `.claude/settings.json`. Mesuré : la lecture de `.env.local` par un script est refusée (`PermissionError`), `.env.example` se lit toujours.
