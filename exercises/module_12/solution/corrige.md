# Corrigé de l'exercice du module 12

Le workflow de ce dossier est une solution possible parmi d'autres. Le critère est
`check.sh` : un workflow écrit autrement passe s'il se comporte de la même façon.

## Le fichier

`.github/workflows/release-notes.yml`, quatre étapes après le déclencheur
`push: tags: ["v*"]` et la permission `contents: write`.

## La garde

```yaml
- name: Check the Claude token
  env:
    CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
  run: |
    if [ -z "$CLAUDE_CODE_OAUTH_TOKEN" ]; then
      echo "::error::CLAUDE_CODE_OAUTH_TOKEN is empty: run claude setup-token, then gh secret set CLAUDE_CODE_OAUTH_TOKEN."
      exit 1
    fi
```

Elle passe avant le `checkout` et l'installation : sans secret, le job s'arrête en
quelques secondes, avec une annotation qui dit quoi faire. La relecture du module laissait
le job vert, parce qu'une pull request sans relecture reste une pull request ; une release
sans notes, elle, est ratée.

## L'installation

```bash
curl -fsSL https://claude.ai/install.sh | bash -s 2.1.314
echo "$HOME/.local/bin" >> "$GITHUB_PATH"
```

La version est fixée, celle du cours. Sans numéro, le runner prend la dernière, et un
changement d'option peut casser le workflow un jour sans que rien n'ait changé dans le
dépôt. `GITHUB_PATH` rend `claude` visible aux étapes suivantes.

## L'appel

```bash
claude -p "Write the release notes of $TAG ... Output only the notes, with no report and no closing remarks." \
  --permission-mode dontAsk \
  --allowedTools "Bash(git log:*),Bash(git show:*)" \
  --max-turns 10 \
  --output-format json < /dev/null > run.json
```

- `$TAG` vient de `env:` (`TAG: ${{ github.ref_name }}`). Écrit directement dans le
  `run:`, `${{ github.ref_name }}` serait recopié dans le script avant son exécution : un nom
  d'étiquette choisi par quelqu'un d'autre deviendrait du shell.
- Deux règles, en lecture. `Bash(git log:*)` autorise aussi `git log --output=<fichier>` ;
  dans un runner jetable, c'est sans conséquence, mais la règle est plus large que son nom.
- « Output only the notes » : c'est ce qui tient les trois listes du `CLAUDE.md` hors des
  notes. Dans mes essais, avec cette phrase, le résultat ne contenait que les notes. Le
  `CLAUDE.md` est chargé quand même, faute de `--bare`, qui demanderait une clé d'API.

## Le contrôle

```bash
jq -e '.is_error == false' run.json > /dev/null
jq -r .result run.json > notes.md
if ! grep -q '^- ' notes.md; then
  echo "::error::No release notes in the answer of claude:"; cat notes.md; exit 1
fi
```

`claude` sort en 0 même quand ses commandes ont été refusées, et `subtype` peut valoir
`success` sur un échec. Le contrôle lit donc `is_error`, puis demande au moins une ligne de
liste dans le résultat : c'est le travail attendu, pas seulement une réponse. Il ne refuse
pas un passage qui a eu un refus : dans mes essais, l'agent tentait parfois une commande
de plus, sans conséquence sur les notes. Un contrôle sur `permission_denials` vide aurait
fait échouer des notes justes.

`set -o pipefail` en tête de l'étape, pour que la commande de `prev` ne masque pas un échec.

## Le précédent

```bash
prev=$(git describe --tags --abbrev=0 --match 'v*' "$TAG^" 2>/dev/null || git rev-list --max-parents=0 HEAD)
```

L'étiquette précédente parmi les ancêtres du commit étiqueté, ou le premier commit du
dépôt. Deux étiquettes poussées d'un coup lancent deux runs, chacun avec son précédent ;
une étiquette posée sur une autre branche n'est pas trouvée, et les notes remontent alors
à l'étiquette commune la plus proche.

## La publication

```yaml
- name: Publish the release
  env:
    GH_TOKEN: ${{ github.token }}
    TAG: ${{ github.ref_name }}
  run: gh release create "$TAG" --title "$TAG" --notes-file notes.md --verify-tag
```

Le jeton du workflow, avec `contents: write`, suffit à créer une release. Le secret de
Claude ne sert qu'à l'étape de `claude -p`, et il n'y a que là qu'il est passé.

## Le passage réel

Avec `check.sh`, sur `v0.2` : 7 secondes, deux tours, les notes en deux groupes (Added, Fixed ; Changed, vide, omis), aucune
des trois listes du `CLAUDE.md`. Une version naïve (garde qui sort en 0, pas de
`--max-turns`, `${{ github.ref_name }}` dans le `run:`, aucun contrôle de `notes.md`) rend
quatre `FAIL`.
