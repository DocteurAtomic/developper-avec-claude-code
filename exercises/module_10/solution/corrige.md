# Corrigé de l'exercice du module 10

Un skill possible est dans ce dossier : `SKILL.md` et `check_export.py`, à copier dans
`.claude/skills/monthly-export/`. D'autres sont possibles : le critère vérifie des codes de
sortie et les commandes lancées par la session ; le texte des fichiers n'entre pas en compte.

## Le script

`check_export.py` lance l'export par `python -m pachaplan.cli`, avec l'interpréteur qui
l'exécute. Lancé par `uv run python` depuis une autre copie du dépôt, cet interpréteur est
celui de cette copie, qui importe son propre `pachaplan` : c'est ce qui lui fait voir la fin
de mois fausse de `module-05-start`. Il lit la base relative au dossier courant, en lecture
seule (`mode=ro`), et compare les deux totaux tels qu'ils s'impriment, à deux décimales.

```text
$ uv run python .claude/skills/monthly-export/check_export.py 2026-03; echo $?
2026-03  export 3067814.48  invoices 3067814.48  OK
0
$ (cd ../m05 && uv run python "$S" 2026-03; echo $?)
2026-03  export 3046175.50  invoices 3067814.48  DIFFERENT
1
$ uv run python .claude/skills/monthly-export/check_export.py 2026-13; echo $?
usage: check_export.py YYYY-MM
2
```

L'écart de mars, 21 638,98, est celui du module 5 : les douze factures du 31.

## Le `SKILL.md`

Il dit quand l'utiliser (avec les demandes qui doivent le déclencher, et la frontière avec
`relances`), lance le script, et n'écrit l'export qu'après un code 0. Il prévient du défaut
de `-o`, qui vide le fichier visé avant de lire la base. `allowed-tools` pré-approuve le
script, `mkdir -p exports` et l'écriture dans `exports/` : sous `claude -p`, en mode par
défaut, rien d'autre ne passe.

## Une session neuve

Avec ce corrigé, `claude -p "/monthly-export 2026-03"` a lancé le script (`OK`), vérifié que
`exports/` n'existait pas, créé le dossier et écrit `exports/2026-03.csv` (2 210 lignes,
total 3 067 814,48). Le skill écrit par l'agent dans mes essais n'avait pas de ligne
`allowed-tools`, le mode auto lui ayant refusé de l'écrire : la même demande y a vu ses
commandes refusées, et `check.sh` a rendu `FAIL` sur son dernier contrôle. La ligne
ajoutée à la main, les six contrôles sont passés.

Le dossier `exports/` n'est pas dans `.gitignore` : ne le commitez pas.
