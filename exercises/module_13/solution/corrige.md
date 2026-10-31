# Corrigé de l'exercice du module 13

La solution est dans ce dossier : `src/pachaplan/mcp_server.py` complet, avec l'outil
ajouté, et `tests/test_mcp_unpaid.py`. D'autres solutions sont possibles : le critère est le script
`check.sh`, et votre code peut différer de celui-ci.

## L'outil

Deux fonctions et un outil, ajoutés au serveur de `module-13-end` :

- `reference_day()` lit `PACHAPLAN_TODAY`, comme la CLI, et prend la date du système
  sinon ;
- `unpaid(conn, today, days, limit)` appelle `planning.unpaid_invoices`, la fonction du
  rapport `unpaid`, et ne garde que le nombre, le solde, la date limite et les `limit`
  factures les plus en retard, réduites à cinq champs plus la prochaine relance ;
- l'outil `unpaid_invoices(days=30, limit=20)`, marqué `READ_ONLY` comme les autres, passe
  par `run()`, donc par `open_read_only`.

Réutiliser `planning.unpaid_invoices` évite d'écrire une seconde fois le calcul du solde
(paiements et avoirs) et du retard : l'outil et la CLI ne peuvent pas diverger.

## Les pièges

- La connexion. Un outil qui ouvre la base par `connect(db_path)` répond juste et passe
  ses tests : `mode=ro` refuse l'`INSERT`. Il accepte en revanche un `ATTACH`, qui crée un
  autre fichier et peut y écrire. `mcp_write_check.py` remplace `open_read_only` par une
  version qui note chaque connexion, appelle chaque outil, et échoue quand un outil n'en a
  ouvert aucune par ce chemin.
- La date. Sans `reference_day()`, l'outil compte au jour de la machine, et le nombre
  diffère de celui de `pachaplan unpaid` lancé avec `PACHAPLAN_TODAY`. Le serveur reçoit
  l'environnement de Claude Code : la variable exportée avant `claude` lui parvient. Le
  client du SDK, lui, ne transmet qu'une poignée de variables ; `check.sh` lui passe
  l'environnement entier pour cette raison.
- La taille. Les 867 lignes complètes font plus de 300 000 caractères. Claude Code les
  aurait rangées dans un fichier, et l'agent aurait dû le relire par morceaux. Avec
  `limit=20`, le résultat fait 3 673 caractères.

## La sortie attendue

```text
OK    .mcp.json declares the pachaplan server (pachaplan-mcp)
OK    unpaid_invoices over stdio: 867 invoices, 3673 characters
OK    every tool goes through open_read_only; INSERT and ATTACH refused
OK    test suite: 77 passed in 1.23s
OK    ruff check
OK    claude mcp get pachaplan: connected
All checks passed.
```

Le nombre de caractères dépend des champs que vous rendez, et celui des tests de ceux que
vous avez écrits. Sur `module-13-end`, sans l'outil, trois contrôles échouent : l'outil
absent, deux fois, et le serveur en attente d'approbation tant que vous ne l'avez pas
approuvé.
