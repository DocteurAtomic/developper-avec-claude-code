# Exercice du module 3

Le service planification de PachaData a gelé le planning de novembre le 29 octobre 2026.
Tous ses rapports se calculent désormais au 2 novembre 2026, quelle que soit la date du
jour. Teena l'a dit à l'équipe, mais le code, le `README` et le
`CLAUDE.md` du module l'ignorent. L'équipe a aussi une convention que rien dans le dépôt
ne montre : toute nouvelle option de la ligne de commande a son test dans
`tests/test_cli.py`, dans le même commit.

Votre travail : apprendre la date et la convention à l'agent par le `CLAUDE.md`, et corriger le
`README`, qui documente une option `--format json` que `pachaplan` n'a pas.

## Le point de départ

```bash
git switch -c exercice-03 module-03-end
uv sync
```

Le `CLAUDE.md` de `module-03-end` est celui de la vidéo 3.3. Il ne dit rien de la date du
planning ni de la convention des tests.

## Les consignes

1. Ajoutez au `CLAUDE.md` la date de référence des rapports, avec sa raison et sa date.
2. Ajoutez la convention de l'équipe sur les options de la CLI.
3. Corrigez le `README`, en français et en anglais, pour qu'il ne documente que des options
   qui existent. Vérifiez chaque commande qu'il donne avant de la garder.
4. Gardez le `CLAUDE.md` sous 40 lignes. Pour chaque ligne que vous ajoutez, demandez-vous
   si l'agent l'aurait trouvée seul en lisant le dépôt.
5. Commitez.

Vous pouvez faire écrire ces changements par l'agent, ou les écrire vous-même. Dans les
deux cas, relisez le diff avant de commiter.

## Le critère

Dans un shell neuf, sans `PACHAPLAN_TODAY` (si vous l'avez exportée pour le cours,
`unset PACHAPLAN_TODAY`), à la racine du dépôt :

```bash
unset PACHAPLAN_TODAY
claude -p "combien de sessions sont sous 50 % pour le planning en cours ?" \
  --allowedTools "Bash(uv run pachaplan:*)"
```

L'agent répond 80. Sans votre `CLAUDE.md`, il prend la date du système et rend un autre
nombre (66 le 30 octobre 2026).

`--allowedTools` autorise `uv run pachaplan` pour cet appel seulement. Sans lui, `claude -p`
démarre en mode Manual, refuse la commande et ne rend aucun nombre, avec ou sans
`CLAUDE.md`.

Ensuite :

```bash
grep -c -- '--format' README.md     # rend 0 (et sort en code 1, ce qui est normal)
wc -l CLAUDE.md                     # moins de 40
PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q   # 8 passed
uv run ruff check                   # 5 erreurs, code 1, comme le CLAUDE.md l'annonce
```

Chaque commande que donne votre `CLAUDE.md` doit rendre ce qu'il annonce : lancez-les une
par une.

## À réfléchir

- Pourquoi le critère vérifie-t-il la date, et pas la façon de lancer les tests ?
- L'agent a-t-il lu `sessions --help` avant de lancer la commande ? Sinon, quelle option
  a-t-il essayée d'abord ?
- La convention sur `tests/test_cli.py` ne se vérifie pas par ce critère. Comment la
  vérifieriez-vous ?
- Votre ligne sur la date sera fausse en décembre. Qu'avez-vous écrit pour que la session qui
  la lira alors le sache ?

## Le corrigé

Dans `corrige/` : un `CLAUDE.md` de référence (30 lignes), le `README` corrigé, et
`corrige.md`, qui dit ce que la vidéo 3.3 a coupé du fichier de `/init` et pourquoi.
