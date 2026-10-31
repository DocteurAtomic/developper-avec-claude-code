# Exercice du module 13

Le service comptable aimerait, lui aussi, poser ses questions à l'agent : combien de
factures restent impayées, lesquelles relancer en premier. Aujourd'hui la réponse passe par
`uv run pachaplan unpaid --days 30`, donc par le shell. Il faut au serveur MCP du projet un
troisième outil, `unpaid_invoices`, en lecture seule comme les deux autres.

## Le départ

Partez de l'étiquette `module-13-end`, la fin du module :

```bash
git switch -c exercise-13 module-13-end
uv sync
export PACHAPLAN_TODAY=2026-11-02
```

Le serveur `pachaplan` est déjà déclaré dans `.mcp.json`. Lancez `claude` une fois dans le
dossier et approuvez-le (« Use this MCP server »), puis vérifiez dans `/mcp` qu'il est
connecté, avec deux outils.

## La demande

Un outil `unpaid_invoices` dans `src/pachaplan/mcp_server.py` :

1. il rend ce que rend `pachaplan unpaid --days N` : le nombre de factures impayées, le
   solde total, et les factures les plus en retard, chacune avec son client, son solde et
   la prochaine relance ;
2. il prend `days` (30 par défaut) et une limite du nombre de factures montrées (20 par
   défaut) ;
3. il ouvre sa connexion par `open_read_only`, comme les deux autres outils, et il est
   marqué en lecture seule (`read_only_hint`) ;
4. un test au moins, et la suite qui reste verte.

## Les consignes

1. Faites-le écrire par Claude, ou écrivez-le vous-même. Relisez la façon dont l'outil
   ouvre la base : un appel direct à `connect()` passerait les tests et laisserait l'outil
   sans le verrou du serveur.
2. La date. La CLI prend la date du jour dans `PACHAPLAN_TODAY` ; l'outil doit faire de
   même, sinon il compte les factures au jour de votre machine.
3. La taille du résultat. Pour 30 jours, la base contient 867 factures impayées ; toutes
   leurs lignes font plus de 300 000 caractères. Au-delà de 50 000, Claude Code range le
   résultat dans un fichier et ne met dans la conversation que son chemin. D'où la limite.
4. Commitez sur votre branche quand le critère passe. `.mcp.json` ne change pas.

## Le critère

```bash
bash <(git show origin/course:exercises/module_13/check.sh)
```

Six contrôles, tous `OK`, et la dernière ligne `All checks passed.` :

- `.mcp.json` déclare le serveur `pachaplan` ;
- par stdio, comme Claude Code le lance, le serveur liste `unpaid_invoices`, marqué en
  lecture seule, et son appel avec `days=30` rend les 867 factures du rapport, montre
  `FA2025-000085`, la plus en retard, et tient sous 50 000 caractères ;
- chaque outil ouvre sa connexion par `open_read_only`, et cette connexion refuse un
  `INSERT` et un `ATTACH` (`mcp_write_check.py`, sur la même branche) ;
- `PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q --fail-on-skip` passe ;
- `uv run ruff check` passe ;
- `claude mcp get pachaplan` montre le serveur connecté.

Le script lit une copie de la base pour le contrôle des connexions et ne modifie pas
`data/pachaplan.sqlite`. Il lance le serveur deux fois, et `claude mcp get` une fois, qui
démarre lui aussi le serveur pour le contrôler ; il ne lance pas de session `claude`.

Ensuite, dans une session, posez la question du service comptable, par exemple « Combien
de factures sont impayées depuis plus de 30 jours, et lesquelles relancer d'abord ? », et
comparez le nombre avec celui de `uv run pachaplan unpaid --days 30`.
