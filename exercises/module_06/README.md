# Exercice du module 6

Deux demandes arrivent le même jour, et vous les menez de front, chacune dans son worktree.

- Le service planification veut, à la fin du rapport `sessions`, le nombre de sessions
  listées par domaine.
- La comptabilité veut le rapport `unpaid` trié des factures les plus récentes aux plus
  anciennes.

Puis la comptabilité change d'avis, et vous annulez son tri par un `git revert`.

## Le départ

Partez de l'étiquette `module-06-start`, celle du début du module, et non de sa fin : le
réglage `worktree.baseRef` n'y est pas encore, c'est à vous de le poser.

```bash
git switch -c exercice-06 module-06-start
uv sync
export PACHAPLAN_TODAY=2026-11-02
git status          # doit être vide
```

## Les consignes

1. Dans `.claude/settings.json`, ajoutez au même niveau que `permissions` :

   ```json
   "worktree": {
     "baseRef": "head"
   }
   ```

   Vérifiez que le fichier est toujours du JSON valide (`python3 -m json.tool .claude/settings.json`),
   puis commitez-le sur `exercice-06`. Sans ce réglage, vos worktrees partiraient de
   `origin/main` et non de votre branche.

2. Dans un terminal, ouvrez le premier worktree :

   ```bash
   claude --worktree domaines
   ```

   Vérifiez d'abord où il part (`!git log --oneline -2` : votre commit du réglage en tête),
   puis tapez :

   ```text
   Le service planification veut, à la fin du rapport sessions, le nombre de sessions listées par domaine : une ligne par domaine, au format « domain BI: 12 », triées par code de domaine. Ajoute un test et commite.
   ```

3. Dans un second terminal, sans attendre la fin du premier, le second worktree :

   ```bash
   claude --worktree recentes
   ```

   ```text
   La comptabilité veut le rapport unpaid trié des factures les plus récentes aux plus anciennes, puis par numéro de facture. Ajoute un test et commite.
   ```

4. Relisez chaque commit avant de le fusionner (`git show --stat worktree-domaines`, puis
   `git show worktree-domaines`). Puis, depuis le dossier principal, sur `exercice-06` :

   ```bash
   git merge --no-ff worktree-domaines
   git merge --no-ff worktree-recentes
   ```

   Si une fusion bute sur un conflit (le nombre de tests dans `CLAUDE.md`, par exemple, si
   un agent l'a mis à jour), demandez à l'agent de le résoudre et relisez sa résolution avant
   de la commiter.

5. La comptabilité répond que ses relances partent du plus ancien retard : elle veut
   l'ancien ordre. Annulez le commit du tri, le commit de la branche `worktree-recentes` et
   non sa fusion, par un `git revert`, vous-même ou par l'agent.

6. Fermez les deux sessions par `/exit` et supprimez les worktrees. Le menu vous dira que les
   commits seront perdus : vérifiez par `git log --oneline --graph` qu'ils sont bien sur
   `exercice-06` avant de répondre. Si un worktree reste verrouillé, `git worktree unlock`
   puis `git worktree remove`.

## Le critère

```bash
bash <(git show origin/course:exercises/module_06/check.sh)
```

Le script affiche une ligne par contrôle, `OK` ou `FAIL`, et sort en code 1 si l'un échoue :

- deux commits de fusion depuis `module-06-start`, et au moins un revert ;
- `git worktree list` ne montre plus que le dossier principal ;
- `worktree.baseRef` vaut `"head"` dans `.claude/settings.json` ;
- `PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q` passe, sans test sauté ;
- `uv run pachaplan unpaid --days 30` affiche exactement ce qu'il affichait à
  `module-06-start` ;
- `uv run pachaplan sessions --below 50` finit par une ligne par domaine, et chaque compte
  égale celui que `sqlite3` calcule sur les sessions du rapport.

Tout est bon quand la dernière ligne est `All checks passed.`

## À réfléchir

- Le message de chaque commit de l'agent dit-il ce qui a été fait, ou ce qui était voulu ?
- Qu'aurait contenu le worktree `domaines` sans le réglage de l'étape 1 ? Et sur le dépôt du
  cours, où `origin/main` avance avec les modules publiés ?
- Pourquoi annuler le commit du tri plutôt que la fusion qui l'a amené ?
