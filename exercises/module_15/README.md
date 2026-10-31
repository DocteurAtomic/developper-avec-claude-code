# Exercice du module 15

Deux développeurs arrivent lundi. Avant de leur confier le dépôt, l'équipe veut une revue
de sécurité de la configuration Claude Code de `pachaplan` : ce que chaque fichier laisse
faire à l'agent, ce qui le tient, et ce qu'on change avant de la partager. Faites cette
revue, écrivez-la, et appliquez ce que vous marquez « avant de partager ».

## Le point de départ

```bash
git switch -c exercice-15 module-15-end
uv sync
export PACHAPLAN_TODAY=2026-11-02
git show origin/course:exercises/module_15/SECURITY-REVIEW.md > SECURITY-REVIEW.md
```

`module-15-end` contient le bac à sable du projet, réglé dans la vidéo 15.2, et la section
« Sandbox » du `CLAUDE.md`. Le modèle `SECURITY-REVIEW.md` donne les sept sections de la
revue et les six champs de chaque trouvaille.

## Le périmètre de la revue

Tout ce qui part avec le dépôt et que Claude Code lit ou exécute :

- `.claude/settings.json`, ses règles `allow` et `deny`, ses hooks et son bac à sable ;
- `.claude/hooks/`, `.mcp.json` et le serveur qu'il lance ;
- `.claude/skills/relances/` et `.claude/agents/doc-checker.md` ;
- `scripts/monday-note.sh` et `.github/workflows/claude-review.yml` ;
- `.gitignore`, et ce qui reste sur le poste de chacun (`.env`, `.claude/settings.local.json`,
  `~/.claude/settings.json`).

Pour chaque trouvaille, nommez la jambe du modèle de menace qu'elle concerne (données
privées, contenu non fiable, sortie, ou exécution de code), et dites ce qui la tient :
une mécanique, une consigne, ou rien. Une trouvaille tenue par une consigne n'est pas
forcément à corriger, mais elle doit être nommée comme telle.

Vous pouvez demander la revue à l'agent. Relisez alors ce qu'il écrit comme vous reliriez
celle d'un collègue : ce qu'il affirme d'un fichier se vérifie dans le fichier, ce qu'il
affirme de Claude Code se vérifie dans la documentation ou par une commande. Ne modifiez
pas `data/pachaplan.sqlite`, et ne lancez pas de session en `bypassPermissions` pour
tester une règle.

## Le critère

Deux parties. La première se vérifie par une commande, depuis la racine du dépôt :

```bash
bash <(git show origin/course:exercises/module_15/check.sh)
```

Six contrôles, chacun `OK` ou `FAIL` : les sept sections ont chacune au moins une
trouvaille ; il y a au moins dix trouvailles, chacune avec ses six champs et des valeurs
prises dans les listes du modèle ; les sept points de la grille ci-dessous sont dans la
revue ; au moins deux changements sont marqués « avant de partager », et le fichier que
chacun nomme a bien changé depuis `module-15-end` ; `.claude/settings.json` est un JSON
valide, sans règle de chemin `Write(...)` ni `Glob(...)` ; le projet est intact (tests,
`ruff`, empreinte de la base). Le script lit des fichiers et lance les tests, il ne lance
aucune session.

La seconde est la grille. Le script vérifie qu'un point est nommé, il ne juge pas votre
décision : comparez la vôtre.

| Point | Ce qui se passe | Décision attendue | Accepté aussi |
|---|---|---|---|
| Le refus de `git push` | la règle compare le texte : `git -C . push` ne la déclenche pas | accepté, en disant que le bac à sable et la protection de branche tiennent le push | plus tard |
| `mcp__pachaplan__*` | tout outil ajouté au serveur sera autorisé sans relecture | avant de partager : les deux outils par leur nom | accepté, si une revue de code protège `src/pachaplan/mcp_server.py` |
| Hooks et `.mcp.json` en `claude -p` | ils tournent dans un dossier jamais approuvé, et la question de confiance ne les liste pas | accepté pour nos fichiers, avec une relecture de `.claude/` dans chaque revue | plus tard |
| `.env.local` | ni le refus `Read(./.env)` ni le `.gitignore` ne le couvrent | avant de partager : `.env.*` refusé et ignoré, `.env.example` lisible | aucun |
| `.claude/settings.local.json` | ignoré seulement par le `.gitignore` global du poste | avant de partager : ajouté au `.gitignore` du projet | aucun |
| Le bac à sable absent | sans `bubblewrap`, ou sous Windows natif, les commandes tournent sans lui, sans avertissement en session | plus tard, ou un réglage personnel (`failIfUnavailable`) | `strictAllowlist` personnel, si votre trouvaille concerne l'auto mode |
| `.venv` | une commande du bac à sable y écrit, et les hooks et le serveur MCP exécutent ce Python hors du bac à sable | avant de partager : `denyWrite` sur `./.venv` | aucun |

## Un indice, pas un critère

Un changement « avant de partager » se rejoue. Pour le `.env.local` :

```bash
printf 'API_TOKEN=essai\n' > .env.local
claude -p "Lance python3 -c \"print(open('.env.local').read())\" et montre-moi la sortie." \
  --allowedTools "Bash(python3:*)"
git status --short .env.local      # après votre changement, rien : le fichier est ignoré
rm .env.local
```

Avant votre changement, la sortie montre le jeton. Après, `PermissionError`. Le
résultat d'une session reste un indice : le refus tient à la configuration, la phrase
de l'agent dépend du modèle.

## À réfléchir

- Combien de vos trouvailles sont tenues par une consigne ? Pour laquelle accepteriez-vous
  de payer une mécanique ?
- Que changerait, dans votre revue, un réglage géré par l'entreprise
  (`/etc/claude-code/managed-settings.json`) avec `allowManagedPermissionRulesOnly` ?
- Le workflow `claude-review.yml` tourne sur un runner GitHub. Le bac à sable du dépôt
  s'y applique-t-il ? Comment le vérifieriez-vous ?

## Le corrigé

Dans `solution/corrige.md`, avec la revue écrite dans mes répétitions et le patch des
changements.
