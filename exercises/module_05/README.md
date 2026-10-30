# Exercice du module 5

Une demande du service planification, menée de l'interview au test : une commande
`uv run pachaplan cancel-candidates` qui liste les sessions qu'il faudrait peut-être annuler.

## Le point de départ

```bash
git switch -c exercice-05 module-05-end
uv sync
export PACHAPLAN_TODAY=2026-11-02
```

`module-05-end` contient l'export corrigé de la démonstration, et 13 tests.

## Les règles du service

Le service a déjà répondu aux questions qu'on lui a posées. Ce sont ses règles, et ce sont
vos réponses quand l'agent vous interroge :

- les sessions qui commencent entre la date de référence et quinze jours plus tard, les deux
  dates comprises (du 2 au 17 novembre 2026 avec la date du cours) ;
- les sessions qui ne sont pas annulées ;
- celles qui sont remplies strictement sous 40 % : les inscriptions actives (ni annulées, ni
  en liste d'attente) rapportées au nombre de places du cours ;
- une ligne par session, `identifiant;date;titre;inscrits;places`, rien d'autre sur la sortie
  standard, triées par date puis par identifiant. Par exemple :

  ```text
  17663;2026-11-02;Azure: the fundamentals;0;12
  ```

- pas d'option pour l'instant.

Si l'agent pose une question à laquelle ces règles ne répondent pas, répondez comme vous le
feriez pour un vrai service, et notez votre réponse.

## Les consignes

1. Dans une session, passez en plan mode (`Shift+Tab` jusqu'à « plan mode on »), puis :

   ```text
   Le service planification veut une commande cancel-candidates qui liste les sessions qu'il faudrait peut-être annuler. Interviewe-moi avant de proposer quoi que ce soit, puis propose un plan avec ses tests.
   ```

   Ne donnez pas les règles d'un bloc : laissez l'agent poser ses questions, et répondez à
   chacune avec la règle qui convient.

2. Lisez le plan avant de l'approuver. Les tests qu'il propose couvrent-ils les deux bornes
   de la fenêtre, et un taux d'exactement 40 % ? Corrigez par « Tell Claude what to change »
   tant que ce n'est pas le cas.

3. Approuvez, laissez-le coder et tester. Demandez-lui de vous montrer ses nouveaux tests en
   échec avant la correction, s'il ne le fait pas de lui-même.

4. Seulement à la fin, copiez les tests du service dans le projet. Ils vérifient que
   l'interview a bien fixé ce que le service voulait :

   ```bash
   git show origin/course:exercises/module_05/test_cancel_candidates.py > tests/test_cancel_candidates.py
   ```

   (Ou copiez le fichier depuis GitHub, branche `course`.)

## Le critère

```bash
PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q
```

Tous les tests passent, aucun sauté : les 13 de départ, ceux de l'agent, et les 5 de
`tests/test_cancel_candidates.py`.

Puis la liste des identifiants égale celle d'une requête qui ne passe pas par votre code :

```bash
diff <(uv run pachaplan cancel-candidates | cut -d';' -f1) \
     <(sqlite3 -readonly data/pachaplan.sqlite "
SELECT s.session_id
FROM session s JOIN course c ON c.course_id = s.course_id
WHERE s.start_date BETWEEN '2026-11-02' AND date('2026-11-02', '+15 days')
  AND s.status_code <> 'CANCELED'
  AND 100.0 * (SELECT COUNT(*) FROM enrollment e
               WHERE e.session_id = s.session_id
                 AND e.cancellation_date IS NULL AND e.waiting_list = 0)
      / c.max_attendees < 40
ORDER BY s.start_date, s.session_id;") && echo IDENTIQUES
```

`diff` ne doit rien afficher d'autre que `IDENTIQUES`. Avec la base du cours, la liste compte
22 sessions.

## À réfléchir

- Quelles questions l'agent a-t-il posées que les règles du service ne tranchaient pas ?
  Qu'avez-vous répondu ?
- Le plan proposé avait-il un défaut que vous avez corrigé avant le code ?
- Les tests du service sont-ils tous passés du premier coup ? Si l'un a échoué, quelle
  question de l'interview aurait dû le prévenir ?

## Le corrigé

Dans `solution/corrige.md` : la session de mes répétitions, les questions de l'agent et mes
réponses. `solution/cancel-candidates.patch` est une solution qui passe le critère ; la vôtre
n'a pas à lui ressembler.
