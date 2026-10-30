# Exercice du module 2

L'équipe a pris goût au fichier de réglages du projet et vous demande d'aller un peu plus
loin. Elle veut que l'agent puisse lancer `ruff` sans demander, qu'il ne touche jamais au
dossier `data/`, où vit la base de référence, et qu'il ne supprime aucun fichier par `rm`.
Et pour que les modifications de code ne demandent plus une approbation à chaque fichier,
le projet démarre désormais en mode `acceptEdits`.

## Le point de départ

```bash
git switch -c exercice-02 module-02-end
uv sync
export PACHAPLAN_TODAY=2026-11-02
```

`module-02-end` contient le `.claude/settings.json` de la vidéo 2.4 : les tests autorisés,
le push et la lecture de `.env` refusés.

## Les consignes

1. Ajoutez au `.claude/settings.json` une règle qui autorise `uv run ruff`, et elle seule.
   Pas `uv run` tout court : relisez la vidéo 2.3 si vous hésitez.
2. Refusez toute écriture dans `data/` par les outils de fichiers de l'agent. Attention, une
   règle `Write(...)` est acceptée par Claude Code mais ne correspond jamais à rien : c'est
   `Edit(...)` qui couvre les écritures.
3. Refusez `rm` par Bash.
4. Faites démarrer le projet en `acceptEdits`, par la clé `permissions.defaultMode`.
5. Le fichier reste du JSON strict : pas de commentaire, pas de virgule en trop.
6. Commitez.

Vous pouvez écrire le fichier vous-même ou le faire proposer par l'agent. Il ne pourra pas
l'écrire seul : `.claude/` est un chemin protégé, et l'écriture vous sera demandée.

## Le critère

Le dossier doit être approuvé : si vous n'avez jamais lancé `claude` dans ce clone, lancez-le
une fois, acceptez la boîte d'approbation, quittez. Puis, à la racine du dépôt :

```bash
claude -p "lance uv run ruff check" < /dev/null 2> erreurs.txt
grep -c "not been trusted" erreurs.txt      # 0 (et code 1, normal quand grep ne trouve rien)
```

La réponse donne les cinq erreurs de `ruff`. Ensuite :

```bash
claude -p "écris OK dans tmp/note.txt" < /dev/null
cat tmp/note.txt                            # OK : le mode acceptEdits est actif

claude -p "écris OK dans data/note.txt" < /dev/null
ls data/note.txt                            # échoue : le fichier n'existe pas

claude -p "supprime le fichier tmp/note.txt" < /dev/null
cat tmp/note.txt                            # OK : le fichier est toujours là

sha256sum data/pachaplan.sqlite
# 793308b2e47ad90b435cc877819f198f569aa3dc9933650de7f2494c686519c2
```

`tmp/` est ignoré par le `.gitignore` du dépôt : supprimez-le vous-même à la fin
(`rm -r tmp erreurs.txt`).

Les quatre appels doivent rendre ce qui est annoncé. Une épreuve qui passe pour une mauvaise
raison ne compte pas : le refus dans `data/` doit venir de votre règle, pas d'un mode qui
refuse tout.

## À réfléchir

- Sans la consigne 4, l'écriture dans `data/note.txt` aurait aussi été refusée. Pourquoi ?
  Qu'est-ce que l'écriture dans `tmp/` vérifie, que celle de `data/` ne vérifie pas ?
- Pourquoi la règle sur `rm` devient-elle nécessaire dès que le projet passe en
  `acceptEdits` ?
- `defaultMode` à `auto` dans le fichier du projet n'aurait eu aucun effet. Pourquoi
  Claude Code refuse-t-il qu'un dépôt choisisse ce mode-là pour vous ?
- L'agent pourrait-il écrire dans `data/` autrement que par ses outils de fichiers ? Par
  quel moyen, et qu'est-ce qui l'en empêcherait ?

## Le corrigé

Dans `solution/` : `settings.json`, le fichier de référence, et `corrige.md`, qui explique
chaque règle et ce que chaque épreuve du critère vérifie.
