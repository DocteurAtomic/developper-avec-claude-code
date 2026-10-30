# Développer avec Claude Code : exercices

Branche des exercices du cours en ligne « Développer avec Claude Code » de Docteur Atomic
(https://www.docteuratomic.com). The English version follows the French one.

## Français

Le projet du cours, `pachaplan`, est sur la branche `main`. Cette branche-ci ne contient que
les énoncés, les fichiers de départ et les corrigés des exercices, un dossier par module
(`exercises/module_03/`). Elle est séparée de `main` pour que Claude Code, quand il lit le
projet, n'y trouve rien qui lui dise que c'est un cours.

Pour suivre un module :

```bash
git clone https://github.com/DocteurAtomic/developper-avec-claude-code.git
cd developper-avec-claude-code
git switch -c module-03 module-03-start     # le projet tel qu'il est au début du module
export PACHAPLAN_TODAY=2026-11-02           # la date à laquelle le cours est mesuré
uv sync
```

L'énoncé se lit sur GitHub, ou dans un autre dossier :
`git worktree add ../exercices course`.

Chaque module part de son étiquette `module-NN-start`, sur une branche à son nom : votre
travail d'un module reste sur sa branche, et le module suivant repart de l'état de référence.

## English

The course project, `pachaplan`, is on the `main` branch. This branch only holds the
statements, starting files and solutions of the exercises, one folder per module
(`exercises/module_03/`). It is kept apart from `main` so that Claude Code, reading the
project, finds nothing telling it that this is a course.

To follow a module:

```bash
git clone https://github.com/DocteurAtomic/developper-avec-claude-code.git
cd developper-avec-claude-code
git switch -c module-03 module-03-start     # the project as it is at the start of the module
export PACHAPLAN_TODAY=2026-11-02           # the date the course is measured at
uv sync
```

Read the statement on GitHub, or in another folder: `git worktree add ../exercises course`.

Each module starts from its `module-NN-start` tag, on a branch named after it: your work on a
module stays on its branch, and the next module starts again from the reference state.

## Licence / License

MIT, see `LICENSE`.
