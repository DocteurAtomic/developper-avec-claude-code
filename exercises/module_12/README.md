# Exercice du module 12

À chaque version, quelqu'un de l'équipe écrit à la main les notes de version à partir du
journal Git. L'équipe veut qu'elles s'écrivent seules quand une étiquette `v*` est poussée,
et qu'elles soient publiées comme release GitHub. Une version publiée sans notes est une
erreur : contrairement à la relecture du module, ce workflow doit échouer quand il ne peut
pas faire son travail.

## Le départ

Partez de l'étiquette `module-12-end`, la fin du module :

```bash
git switch -c exercise-12 module-12-end
uv sync
export PACHAPLAN_TODAY=2026-11-02
```

## La demande

Un workflow `.github/workflows/release-notes.yml` :

1. déclenché par `push: tags: ["v*"]` ;
2. une première étape de garde, qui échoue (code 1, et un message qui dit quoi faire) quand
   le secret `CLAUDE_CODE_OAUTH_TOKEN` est vide ;
3. une étape qui installe Claude Code (`curl -fsSL https://claude.ai/install.sh | bash -s
   <version>`), puis une étape qui lance `claude -p` en `--permission-mode dontAsk`, avec
   `--max-turns` et des règles `--allowedTools` limitées à la lecture de l'historique Git ;
4. cette étape écrit les notes dans `notes.md`, et elle échoue quand `claude` sort en 0
   sans les avoir écrites ;
5. les valeurs de GitHub (`${{ github.ref_name }}`, le secret) passent par `env:`, jamais
   directement dans un `run:` ;
6. une dernière étape publie la release (`gh release create`), avec la permission
   `contents: write`.

## Les consignes

1. Faites écrire le workflow par Claude, ou écrivez-le vous-même. Si c'est Claude, relisez
   ce qu'il passe à `claude -p` : le `CLAUDE.md` du projet lui demande trois listes à la fin
   de chaque tâche, et elles n'ont rien à faire dans des notes de version.
2. Le contrôle de l'étape `claude -p`. Le code de sortie ne suffit pas : en `dontAsk`, une
   session dont les commandes ont été refusées sort en 0. Lisez le JSON
   (`--output-format json`), puis vérifiez que `notes.md` contient bien des notes.
3. Le précédent. Les notes portent sur les commits depuis l'étiquette précédente :
   `git describe --tags --abbrev=0 --match 'v*' "$TAG^"`, et le premier commit du dépôt
   quand il n'y en a pas. Il faut `fetch-depth: 0` au `checkout`, sinon le runner n'a ni
   l'historique ni les étiquettes.
4. Commitez le workflow avant de poser l'étiquette : le workflow qui tourne est celui du
   commit étiqueté.

## Le critère

En local, sans GitHub, avec deux étiquettes posées dans votre clone :

```bash
git tag v0.1 module-10-end
git tag v0.2 HEAD
bash <(git show origin/course:exercises/module_12/check.sh)
```

Sept contrôles, tous `OK`, et la dernière ligne
`All checks passed. The notes are in notes-v0.2.md.` : le workflow se déclenche sur une
étiquette ; `claude -p` tourne en `dontAsk` avec une limite de tours ; la garde échoue sans
jeton et passe avec ; l'étape de `claude -p` échoue quand un faux `claude` sort en 0 après un
refus ; un vrai passage sur `v0.2` écrit `notes.md`.

Le script lit votre workflow avec PyYAML (par `uv run --with pyyaml`), découpe la garde et
l'étape de `claude -p`, et les lance comme le runner, dans un `git worktree` temporaire sur
l'étiquette. Le vrai passage est une session `claude -p`, sur votre connexion. Le script ne
pousse rien et ne publie rien ; il retire le worktree à la sortie. Il refuse aussi
`bypassPermissions` et un `${{ }}` dans un `run:`.

Sur GitHub, si vous avez fait la vidéo 12.2, dans votre dépôt `mon-pachaplan` :

```bash
git push github exercise-12
git tag v1.0 && git push github v1.0
gh run list --workflow release-notes.yml --limit 1     # completed success
gh release view v1.0                                   # les notes
gh secret delete CLAUDE_CODE_OAUTH_TOKEN
git tag v1.1 && git push github v1.1
gh run list --workflow release-notes.yml --limit 1     # completed failure
gh run view --log-failed | head                        # l'erreur de la garde
```

Remettez ensuite le secret (`gh secret set CLAUDE_CODE_OAUTH_TOKEN`).

## À réfléchir

- La garde de la relecture laisse le job vert, celle des notes le fait échouer. Qu'est-ce
  qui justifie la différence ?
- Comment évitez-vous que les trois listes du `CLAUDE.md` finissent dans les notes ?
- Que se passe-t-il si quelqu'un pousse deux étiquettes d'un coup ? Et si l'étiquette
  précédente n'est pas un ancêtre de la nouvelle ?
