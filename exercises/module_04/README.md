# Exercice du module 4

Trois tâches, chacune dans le mode qui lui convient : une question posée par `claude -p`,
une modification lancée en session puis annulée, et un résumé du journal Git envoyé par un
tuyau.

## Le point de départ

```bash
git switch -c exercice-04 module-04-end
uv sync
export PACHAPLAN_TODAY=2026-11-02
```

`module-04-end` contient la colonne du formateur de la vidéo 4.4. À la fin de
l'exercice, le dépôt revient à l'état de l'étiquette.

## Les consignes

1. Une question. Par `claude -p`, depuis la racine du dépôt :

   ```bash
   claude -p "combien de sessions commencent en novembre 2026 ?"
   ```

   Regardez ce qu'il répond. `claude -p` démarre en mode Manual, et le projet n'autorise que
   la suite de tests. Relancez avec `--allowedTools`, en autorisant la seule commande dont
   l'agent a besoin pour lire la base sans l'écrire.

2. Une modification annulée. Dans une session (`claude`) :

   ```text
   ajoute au rapport unpaid une colonne avec le pays du client
   ```

   Laissez-le faire, puis considérez que le service a changé d'avis. Annulez par `/rewind`
   (`Esc` deux fois sur une saisie vide), en choisissant ce prompt et « Restore code and
   conversation » si le menu le propose.

3. Un tuyau. Hors de toute session :

   ```bash
   git log --oneline | claude -p "résume ce journal en deux phrases pour le service planification"
   ```

## Le critère

La réponse de la tâche 1 donne le même nombre que :

```bash
sqlite3 -readonly data/pachaplan.sqlite \
  "SELECT COUNT(*) FROM session WHERE start_date >= '2026-11-01' AND start_date < '2026-12-01';"
```

Après la tâche 2 :

```bash
git status --porcelain     # aucune ligne
sha256sum data/pachaplan.sqlite
# 793308b2e47ad90b435cc877819f198f569aa3dc9933650de7f2494c686519c2
```

Si `git status` montre encore des fichiers après le `/rewind`, c'est que l'agent les a écrits
par Bash : `git restore .` les remet en place. Notez lesquels avant.

Pour la tâche 3, gardez la commande et sa sortie.

## À réfléchir

- À la tâche 1, sans autorisation, l'agent a-t-il donné un nombre ? Qu'a-t-il proposé ?
- Pourquoi autoriser `sqlite3 -readonly` plutôt que `sqlite3` tout court ?
- À la tâche 2, qu'annonçait le menu de `/rewind` sous votre prompt ? Correspondait-il à ce
  que `git status` a montré ensuite ?
- Pourquoi la tâche 3 n'a-t-elle besoin d'aucune permission ?

## Le corrigé

Dans `solution/corrige.md` : les commandes, les sorties de mes répétitions et ce qu'elles montrent.
