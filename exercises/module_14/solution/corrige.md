# Corrigé de l'exercice du module 14

Joué le 31 octobre 2026 avec Claude Code 2.1.316, dans une session interactive en auto
mode, partie de `module-14-end`, avec le `CLAUDE.md` personnel et la boîte de leçons de la
vidéo 14.3. Une phrase par correction, tapée telle quelle. Vos fichiers ne seront pas les
miens : le critère est `check.sh` et la grille de l'énoncé.

## Les cinq prompts

```text
Mets dans mon CLAUDE.md personnel : quand je demande une relecture, commence par la liste des problèmes, sans résumé du code.
Retiens ça pour ce projet : le service planification gèle le planning de décembre 2026 à partir du 15 novembre. Après cette date, aucune affectation de formateur de décembre ne bouge sans son accord.
C'est une leçon : uv run pytest -q -k export_febuary a rendu 75 deselected et un code de sortie 5, le filtre mal orthographié ne sélectionnait aucun test. Un filtre de tests se donne avec le nombre de tests qu'il doit trouver.
Fais-en un skill du projet, trainers-week, dans .claude/skills/ : chaque vendredi, le service planification veut la liste des formateurs en service la semaine suivante, du lundi au vendredi, jour par jour, avec les avertissements. Ne commite pas.
uv.lock ne s'édite jamais à la main, seul uv le modifie. Ajoute une règle deny dans .claude/settings.json.
```

## La session

1. La préférence. Première lecture hors du dossier de travail : Claude Code demande la
   permission de lire `~/.claude/CLAUDE.md`. J'ai répondu « Yes, but ask again next
   time ». Une ligne ajoutée dans la section des réponses, relue par `grep`.
2. Le gel. « wrote 1 memory » : un fichier `gel-planning-decembre-2026.md`, de type
   `project`, et sa ligne dans `MEMORY.md`. Il note de lui-même que la date s'entend à la
   date de référence et que le fait sera périmé après décembre. Il signale aussi la limite :
   rien dans le code n'empêche de modifier une affectation.
3. La leçon. Il relance la commande pour recopier la vraie sortie (`75 deselected in
   0.36s`, code 5) et écrit les quatre lignes à la fin de `LESSONS.md`.
4. Le skill. Deux minutes quarante. Un `SKILL.md` dont la description cite les demandes
   (« les formateurs de la semaine prochaine »), un script `scripts/trainers_week.py` qui
   réutilise le tableau de `pachaplan trainers` pour chaque jour, sept tests, cinq cassures
   du script vues tomber, un `HISTORY.md`, le `README` et le nombre de tests du
   `CLAUDE.md` mis à jour (82). Il a voulu ajouter `Skill(trainers-week)` aux règles
   `allow` : refusé par l'auto mode, et il ne l'a pas contourné. C'est à vous de l'écrire
   si une session `claude -p` doit utiliser le skill.
5. L'interdit. `"Edit(./uv.lock)"` ajouté aux règles `deny`. Cette modification-là est
   passée : elle restreint. Il l'a testée par un `Edit` refusé, « File is in a directory
   that is denied by your permission settings », et `git status` n'a rien montré.

```text
OK    personal CLAUDE.md (…/.claude/CLAUDE.md) has the review preference
OK    auto memory of this project has the December freeze (gel-planning-decembre-2026.md)
OK    LESSONS.md has the lesson on the empty test filter, with Déclencheur, Preuve, Promu
OK    skill trainers-week: description and a body that runs pachaplan trainers
OK    settings.json denies Edit on uv.lock
OK    project intact: 82 passed in 1.23s, ruff clean, database and uv.lock unchanged
All checks passed.
```

Puis la sonde de l'énoncé, en session neuve : `Edit` refusé, même empreinte avant et
après (`33c5edd9…`).

## Mes corrections

Le `SKILL.md` contenait une ligne sur le gel de décembre, recopiée de la mémoire. Un état
qui expire le 1er janvier, écrit dans un fichier versionné que toute l'équipe charge : c'est
la correction 2 rangée une seconde fois, au mauvais étage. Je l'ai retirée. La mémoire
suffit, et si l'équipe doit le savoir, c'est au `CLAUDE.md` du dépôt, avec la date de fin.

La boîte de leçons a reçu trois entrées et non une. Les deux autres, la session les a
ouvertes seule : un `INSERT` positionnel qui avait inversé deux colonnes dans son propre
test, et une façon de tester une règle `deny` sans risque d'écrire. Les deux sont de vraies
leçons de méthode. Mais trois entrées pour une demande, c'est le rythme auquel une boîte
déborde : à la distillation de la semaine, l'une des deux rejoindra sans doute la page
« tests » de votre base, et l'autre restera peut-être une curiosité.

## Les fichiers

- `exercise-14.patch` : ce qui change dans le dépôt (le skill, son script et ses tests,
  la règle `deny`, le `README`, le nombre de tests du `CLAUDE.md`), sans la ligne du gel.
  `git apply` depuis `module-14-end`.
- `claude-config/CLAUDE.md`, `claude-config/LESSONS.md` : mes fichiers personnels à la fin
  de l'exercice, ceux de la vidéo 14.3 avec la préférence et les trois leçons.
- `claude-config/memory/gel-planning-decembre-2026.md` : la note de la mémoire du projet.

## À réfléchir, mes réponses

- La correction 2 : j'ai choisi la mémoire parce que la demande venait de moi, pour mes
  sessions. Si toute l'équipe affecte des formateurs avec l'agent, elle va au `CLAUDE.md`
  du dépôt, avec sa date de fin. Le 2 janvier, dans les deux cas, quelqu'un doit la
  retirer : une mémoire datée se relit à l'élagage.
- La règle sur `uv.lock` n'arrête pas un `sed -i` lancé par Bash, et c'est voulu : `uv add`
  et `uv lock` passent aussi par Bash et doivent pouvoir écrire. Descendre d'un étage
  voudrait dire un hook sur Bash qui reconnaîtrait les commandes, et il raterait les
  scripts. Je n'en ai pas eu besoin.
- Une correction déjà écrite : la date de référence. Elle est dans le `CLAUDE.md` du dépôt
  depuis la vidéo 14.1, et la session qui a écrit le skill l'a reprise dans son
  `SKILL.md` (« never rerun it with `--today` at the clock date »).
