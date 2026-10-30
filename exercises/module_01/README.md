# Exercice du module 1

Trois questions sur `pachaplan`, posées à l'agent dans une session. Pour chacune, vous notez
sa réponse, puis vous la confirmez ou la réfutez par une commande que vous lancez vous-même.

## Le point de départ

```bash
git switch -c exercice-01 module-01-end
uv sync
export PACHAPLAN_TODAY=2026-11-02
```

`module-01-end` est l'état de départ du projet : le module 1 ne modifie pas le code.

## Les consignes

Dans une session (`claude`, à la racine du dépôt), posez les trois questions, une par une :

1. ```text
   Dans ce projet, quelle table et quelle colonne servent à calculer le taux de remplissage d'une session ?
   ```
2. ```text
   Combien de factures la commande unpaid --days 30 rend-elle au 2026-11-02 ?
   ```
3. ```text
   Quel formateur donne la session 17709 ?
   ```

Pour chaque réponse, remplissez une ligne de cette grille, dans un fichier à vous :

| Question | Réponse de l'agent | Commande de vérification | Ce qu'elle rend | Confirmée ou réfutée |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

Les commandes de vérification sont les vôtres. Elles ne passent pas par l'agent : `grep -n`
dans le code, `uv run pachaplan`, ou `sqlite3 -readonly` sur `data/pachaplan.sqlite`. Ne
recopiez pas une commande que l'agent a lancée sans l'avoir relancée vous-même.

## Le critère

La colonne « Ce qu'elle rend » de votre grille contient les trois valeurs justes, et chaque
réponse de l'agent est notée confirmée ou réfutée. Vous pouvez contrôler les valeurs avec :

```bash
grep -n "max_attendees\|waiting_list" src/pachaplan/planning.py
uv run pachaplan unpaid --days 30 | grep "unpaid invoice"
sqlite3 -readonly data/pachaplan.sqlite \
  "SELECT c.first_name, c.last_name FROM session s
   JOIN trainer t ON t.trainer_id = s.trainer_id
   JOIN contact c ON c.contact_id = t.contact_id
   WHERE s.session_id = 17709;"
```

Et le dépôt n'a pas bougé :

```bash
git status --porcelain     # aucune ligne
sha256sum data/pachaplan.sqlite
# 793308b2e47ad90b435cc877819f198f569aa3dc9933650de7f2494c686519c2
```

## À réfléchir

- L'agent a-t-il lancé une commande pour répondre, ou seulement lu le code ? Où le voyez-vous
  à l'écran ?
- A-t-il cité des numéros de ligne ? Correspondent-ils à ceux que donne `grep -n` ?
- Pour la question 2, quelle date a-t-il prise ? Que rend la commande si vous ouvrez un
  terminal neuf sans exporter `PACHAPLAN_TODAY` ?
- Une de ses réponses vous a-t-elle paru juste avant même de la vérifier ? L'était-elle ?

## Le corrigé

Dans `solution/corrige.md` : les valeurs, les commandes et ce que l'agent a répondu dans ma
session.
