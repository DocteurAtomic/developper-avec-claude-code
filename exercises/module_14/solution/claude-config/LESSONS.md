# Leçons à distiller

Boîte de réception. Chaque entrée sera rangée dans ma base de méthode, puis
retirée d'ici.

## Donner un filtre de tests avec le nombre de tests qu'il doit sélectionner, et le vérifier
Déclencheur : un filtre `-k` mal orthographié ne sélectionnait aucun test (pachaplan, 2026-10-31).
Preuve : `uv run pytest -q -k export_febuary; echo "exit=$?"` → `75 deselected in 0.36s` / `exit=5`
Promu : pas encore.

## Nommer les colonnes d'un INSERT écrit dans un test, et lire un premier échec comme un possible bug du test
Déclencheur : un INSERT positionnel a inversé room_id et trainer_id ; le test a échoué à cause de lui, pas du code (pachaplan, 2026-10-31).
Preuve : `uv run pytest -q tests/test_trainers_week_skill.py` → `E  AssertionError: assert '  - session 302: no trainer assigned' in [...]` / `1 failed, 6 passed`
Promu : pas encore.

## Tester une règle deny d'Edit par un Edit dont le texte cherché n'existe pas : refusé si la règle tient, sinon échec sans écriture
Déclencheur : vérification de la règle `Edit(./uv.lock)` ajoutée au deny de `.claude/settings.json` (pachaplan, 2026-10-31).
Preuve : Edit de `uv.lock` avec old_string `CHAINE-ABSENTE-TEST-DENY-7f3a` → `File is in a directory that is denied by your permission settings.` ; `git status --short uv.lock` → vide
Promu : pas encore.
