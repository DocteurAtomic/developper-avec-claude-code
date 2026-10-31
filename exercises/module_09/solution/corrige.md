# Corrigé de l'exercice du module 9

Ce corrigé suit une exécution réelle, la nuit du 30 au 31 octobre 2026, avec Claude Code
2.1.314. Votre sous-agent aura un autre prompt et rendra d'autres phrases : le critère est
le script `check.sh`, plus la grille. Le fichier `solution/test-reviewer.md` est le
sous-agent de cette exécution, à copier dans `.claude/agents/` si vous voulez comparer.

## La création

Le prompt de l'énoncé, par `claude -p` en mode `acceptEdits` : la création est refusée.
`.claude/` est un chemin protégé, et sous `-p` personne ne répond à la demande de
confirmation. Le compte rendu le dit : « Je n'ai pas créé `.claude/agents/test-reviewer.md` :
tu as refusé la demande d'écriture dans `.claude/agents/`. » Le refus figure dans
`permission_denials` de la sortie JSON.

Le même prompt avec `--permission-mode auto` : quarante-sept secondes, un fichier de
quatre-vingt-quatre lignes, `tools: Read, Grep, Glob`, seul fichier modifié, sans commit. Le prompt système interdit d'écrire « passe » ou « échoue » comme si le sous-agent
l'avait vu : il ne peut rien lancer. Il lui demande aussi de ne pas inventer de constat.

## Le lancement

```bash
claude -p "Utilise le sous-agent test-reviewer sur tests/test_unpaid_report.py." \
    --output-format stream-json --verbose < /dev/null > review.jsonl
```

Deux minutes, cinq tours. L'agent principal a délégué à `test-reviewer`, qui n'a utilisé que
`Read` et `Grep`. Puis l'agent principal a lui-même lancé le fichier de tests, avec
et sans `--fail-on-skip`, pour confirmer le premier constat.

```text
$ bash <(git show origin/course:exercises/module_09/check.sh) review.jsonl
OK    .claude/agents/test-reviewer.md exists
OK    name: test-reviewer
OK    a description
OK    read-only tools (Read Grep Glob)
OK    the run launched the test-reviewer subagent
OK    the subagent used only Grep Read
OK    no Edit or Write in the run
OK    src/ and tests/ unchanged since exercise-09-start
All checks passed.
```

## La grille

| Défaut | Trouvé ? | Ligne citée | Preuve donnée |
|---|---|---|---|
| un test qui ne tourne jamais | oui | `:102`, `test_unpaid_matches_the_real_database` | il lit `PACHAPLAN_DATABASE` ; confirmé par l'agent principal : `11 passed, 1 skipped`, et code 1 avec `--fail-on-skip` |
| une assertion qui passerait sur une sortie vide | oui | `:96`, `test_print_unpaid_writes_no_placeholder` | il ne vérifie que l'absence de `None` ; lecture seule |
| un cas trop loin de la limite | oui | `:70` | soixante et un jours de retard pour un seuil à « plus de 15 jours » ; lecture seule |

Le rapport ajoute des constats qui ne sont pas les trois défauts :

| Constat | Vrai ? |
|---|---|
| la requête de référence du test `:102` recopie les seuils du code (`invoice_date <= ?`, `balance > 0.005`) | vrai : une erreur commune aux deux passerait |
| `:38` et `:43` ne distinguent pas l'échéance enregistrée du défaut de trente jours : toutes les factures de la base de test ont une échéance à trente jours | vrai, à vérifier dans `tests/fixture.sql` |
| `:60` et `:65` ne testent ni l'échéance du jour ni un jour de retard | vrai, une limite non testée de plus |
| `:84` n'a pas de solde juste au-dessus de la tolérance de 0,005 | vrai |
| `:91` n'atteint jamais la limite des cinq clients (deux clients) | vrai |

Les trois défauts sont trouvés. Seul le premier a été vérifié par une commande, et par
l'agent principal : le sous-agent ne peut rien lancer, et le compte rendu le range dans « Not
run / not checked ». Les autres constats sont des lectures justes, que l'exercice du module 8
a vérifiées par des cassures pour les deux premiers défauts.

## La barrière

La liste `tools` est la barrière : sans `Bash`, `Edit` ni `Write`, le sous-agent ne peut pas
modifier le dépôt, quoi que dise son prompt. Le prix est qu'il ne prouve rien par
l'exécution, et son rapport dit lui-même ce qu'il n'a pas pu vérifier. Le travail de l'agent
principal, et le vôtre, est de vérifier tout constat qu'une commande peut trancher.
