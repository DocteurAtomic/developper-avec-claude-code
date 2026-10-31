# Exercice du module 14

Cinq corrections, de celles qu'une équipe finit par redonner chaque semaine. Rangez chacune
à l'étage où elle sera relue au bon moment, et écrivez-la. Le geste est celui du module ;
les corrections sont nouvelles.

## Le point de départ

```bash
git switch -c exercice-14 module-14-end
uv sync
export PACHAPLAN_TODAY=2026-11-02
```

`module-14-end` contient le `CLAUDE.md` élagué de la vidéo 14.4 et la règle de chemin
`.claude/rules/mcp-server.md`. Vous aurez besoin d'un `CLAUDE.md` personnel et d'une boîte
de leçons, dans le dossier de configuration de Claude Code (`~/.claude/`, ou celui que
nomme `CLAUDE_CONFIG_DIR` si vous l'avez défini). S'ils n'existent pas encore, les modèles
de la vidéo 14.3 sont à côté de cet énoncé :

```bash
git show origin/course:exercises/module_14/CLAUDE-personnel.md > ~/.claude/CLAUDE.md
git show origin/course:exercises/module_14/LESSONS.md > ~/.claude/LESSONS.md
```

Ces deux commandes écrasent les fichiers s'ils existent : si vous avez déjà un `CLAUDE.md`
personnel, recopiez seulement les sections « Où ranger ce qu'on apprend » et « Les
leçons ».

## Les cinq corrections

1. « Quand je demande une relecture, commence par la liste des problèmes, sans résumé du
   code. »
2. « Le service planification gèle le planning de décembre 2026 à partir du 15 novembre :
   après cette date, aucune affectation de formateur de décembre ne bouge sans son
   accord. »
3. « `uv run pytest -q -k export_febuary` a rendu `75 deselected` et un code de sortie 5 :
   le filtre, mal orthographié, ne sélectionnait aucun test. Un filtre de tests se donne
   avec le nombre de tests qu'il doit trouver. »
4. « Chaque vendredi, le service planification veut la liste des formateurs en service la
   semaine suivante, du lundi au vendredi, jour par jour, avec les avertissements. »
5. « `uv.lock` ne s'édite jamais à la main : seul `uv` le modifie. »

Pour chacune, décidez d'abord de l'étage, en une phrase qui dit pourquoi. Écrivez ensuite,
vous-même ou en demandant à l'agent (« retiens ça pour ce projet », « mets-le dans le
`CLAUDE.md` », « c'est une leçon », « fais-en un skill »). Le skill de la correction 4
s'appelle `trainers-week`, dans `.claude/skills/` du dépôt. Ne modifiez pas
`data/pachaplan.sqlite`, ni `uv.lock`.

## Le critère

Deux parties. La première se vérifie par une commande, depuis la racine du dépôt :

```bash
bash <(git show origin/course:exercises/module_14/check.sh)
```

Elle contrôle que chaque correction est écrite à un endroit qui la recevra, sous une
forme qui tient : la préférence dans le `CLAUDE.md` personnel, le gel dans la mémoire du
projet, la leçon dans la boîte, avec ses lignes `Déclencheur`, `Preuve` et `Promu`, le
skill avec sa description, la règle de permission sur `uv.lock`, et que le dépôt est
intact (tests, `ruff`, empreinte de la base, `uv.lock` intact). Six contrôles, chacun
`OK` ou `FAIL`, et deux `FAIL` de plus si la préférence ou la procédure du vendredi
apparaissent aussi dans le `CLAUDE.md` du dépôt. Elle ne lit que des fichiers et ne lance
aucune session.

La seconde est la grille ci-dessous. Le script vérifie que vous avez écrit quelque chose
au bon endroit, il ne juge pas votre raison : comparez votre phrase à la grille.

| Correction | Étage attendu | Pourquoi | Accepté aussi | À éviter |
|---|---|---|---|---|
| 1. La relecture | `CLAUDE.md` personnel | une préférence à vous, valable dans tous vos dépôts | aucun | le `CLAUDE.md` du dépôt : vos collègues n'ont pas demandé cette forme |
| 2. Le gel de décembre | mémoire du projet | un état de ce projet, daté, qui expirera, et que le code ne dit pas | le `CLAUDE.md` du dépôt, si toute l'équipe doit le savoir, avec la date de fin | la boîte de leçons : ce n'est pas une méthode |
| 3. Le filtre vide | boîte de leçons, quatre lignes, la preuve recopiée | une leçon de méthode, vraie dans tout projet qui a des tests | aucun | la mémoire du projet : elle mourrait avec lui |
| 4. Le vendredi | un skill, `trainers-week` | une procédure qui se refait, qui ne sert qu'un jour par semaine | un skill avec un script, si la boucle sur les jours vous a déjà trahi | le `CLAUDE.md` : relu à chaque session pour une tâche du vendredi |
| 5. `uv.lock` | une règle de permission `deny` | un interdit sur un fichier, qu'aucune session ne doit pouvoir enfreindre par ses outils de fichiers | un hook `PreToolUse`, s'il doit expliquer quoi faire à la place | une consigne seule : elle sera suivie presque toujours |

## Un indice, pas un critère

Une session neuve qui respecte vos règles dit qu'elles sont lues. Elle ne prouve pas
qu'elles tiendront : son résultat dépend du modèle et du jour. Essayez quand même la
règle de permission, la seule des cinq qui ne dépende pas de lui :

```bash
sha256sum uv.lock
claude -p "Avec l'outil Edit, ajoute une ligne vide à la fin de uv.lock." --permission-mode acceptEdits
sha256sum uv.lock      # la même empreinte
```

## À réfléchir

- Pour la correction 2, qu'est-ce qui vous a fait choisir entre la mémoire et le `CLAUDE.md`
  du dépôt ? Que se passe-t-il le 2 janvier ?
- La règle de permission sur `uv.lock` arrête-t-elle une commande `sed -i` lancée par Bash ?
  Faut-il descendre d'un étage de plus ?
- Une de vos cinq corrections était-elle déjà écrite quelque part dans le dépôt ?

## Le corrigé

Dans `solution/corrige.md`, avec les fichiers écrits dans mes répétitions.
