# Exercice du module 10

La comptabilité demande l'export de chaque mois, et le module 5 a montré qu'un export peut
sortir faux sans que rien ne le signale : jusqu'à la correction, mars perdait son dernier
jour. L'équipe veut un skill `monthly-export` qui ne rende un export qu'après l'avoir
comparé aux factures de la base. Le travail est dans un script, que l'on peut lancer seul.

## Le départ

Partez de l'étiquette `module-10-end`, la fin du module :

```bash
git switch -c exercise-10 module-10-end
uv sync
export PACHAPLAN_TODAY=2026-11-02
```

## La demande

Un skill du projet, dans `.claude/skills/monthly-export/`, avec deux fichiers :

- `check_export.py` prend un mois `AAAA-MM`, lance l'export de ce mois, lit le total de la
  ligne `TOTAL` (la dernière colonne) et le compare à la requête de référence du module 5,
  sur la base ouverte en lecture seule :

  ```sql
  SELECT printf('%.2f', SUM(gross_amount)) FROM invoice
  WHERE strftime('%Y-%m', invoice_date) = 'AAAA-MM'
  ```

  Il affiche les deux totaux et sort en 0 s'ils sont égaux, en 1 s'ils diffèrent. Lancé
  par son chemin absolu depuis une autre copie du dépôt, il vérifie le code de cette copie,
  pas celui de la vôtre.
- `SKILL.md` dit quand utiliser le skill, comment lancer le script et quoi faire selon son
  code de sortie. L'export ne s'écrit dans un fichier qu'après un contrôle réussi.

## Les consignes

1. Faites écrire le skill par Claude, ou écrivez-le vous-même. Un prompt possible, en
   session interactive :

   ```text
   Crée un skill du projet, monthly-export, dans .claude/skills/monthly-export/. Il sert quand la comptabilité demande l'export d'un mois. Le travail est dans un script, .claude/skills/monthly-export/check_export.py, qui prend le mois AAAA-MM, lance l'export de ce mois, lit le total de la ligne TOTAL et le compare au résultat de la requête de référence : SELECT printf('%.2f', SUM(gross_amount)) FROM invoice WHERE strftime('%Y-%m', invoice_date) = 'AAAA-MM', sur data/pachaplan.sqlite en lecture seule. Il affiche les deux totaux et sort en 0 s'ils sont égaux, en 1 s'ils diffèrent. Il doit marcher aussi lancé par son chemin absolu depuis une autre copie du dépôt, avec le code de cette copie. Le SKILL.md dit quand utiliser le skill et comment lancer le script. Ne commite pas.
   ```

2. Les pièges connus. `csv.writer` termine ses lignes par `\r\n` : sans le retirer, la
   comparaison échoue sur des montants identiques. Et `pachaplan export -o` écrase le
   fichier qu'on lui donne, en le vidant avant même de lire la base : le `SKILL.md` ne
   doit jamais le pointer sur un fichier existant ni sur `data/`.
3. Lancez le script ici, puis depuis l'état du module 5, où la fin de mois est encore
   fausse :

   ```bash
   uv run python .claude/skills/monthly-export/check_export.py 2026-03; echo $?
   S=$(realpath .claude/skills/monthly-export/check_export.py)
   git worktree add ../m05 module-05-start
   (cd ../m05 && uv run python "$S" 2026-03; echo $?)
   git worktree remove ../m05
   ```

   Le premier sort en 0, le second en 1.
4. Pour qu'une session sous `claude -p`, en mode par défaut, puisse lancer le script, le
   frontmatter du `SKILL.md` le pré-approuve par `allowed-tools`, avec
   `${CLAUDE_SKILL_DIR}` dans le chemin. Dans mes essais, le mode auto a refusé à l'agent
   d'écrire lui-même cette ligne, parce qu'elle change ses propres permissions : ajoutez-la
   à la main si elle manque.
5. Lancez le skill dans une session neuve, en gardant la trace :

   ```bash
   claude -p "/monthly-export 2026-03" --output-format stream-json --verbose \
       < /dev/null > export.jsonl
   ```

## Le critère

```bash
bash <(git show origin/course:exercises/module_10/check.sh) export.jsonl
```

Six contrôles, tous `OK`, et la dernière ligne `All checks passed.` : les deux fichiers
existent ; le script sort en 0 sur 2026-03 ici ; il sort en 1 sur 2026-03 dans un worktree
temporaire à `module-05-start` ; la session a chargé le skill `monthly-export` ; elle a
lancé `check_export.py 2026-03` et reçu sa ligne `OK`. Le script ne compare pas votre code
au corrigé : deux scripts différents passent s'ils rendent les mêmes codes de sortie.

## À réfléchir

- Qu'est-ce qui, dans votre skill, est dans le script, et qu'est-ce qui est resté dans la
  prose du `SKILL.md` ? Lequel des deux un test peut-il casser ?
- Votre script lit-il le total de la ligne `TOTAL` tel que l'export l'imprime, ou le
  recalcule-t-il ? Que vérifierait-il dans le second cas ?
- Commencez un `HISTORY.md` pour ce skill : la première entrée, et ce que vous avez mesuré.
