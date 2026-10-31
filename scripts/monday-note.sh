#!/usr/bin/env bash
# Monday note of the planning team, run by cron every Monday at 7:00. Cron's PATH
# is short: give it the directories of claude, uv and jq.
#   PATH=/home/me/.local/bin:/usr/local/bin:/usr/bin:/bin
#   0 7 * * 1  bash /path/to/pachaplan/scripts/monday-note.sh
# Fails unless reports/note-DAY.md exists with its "## Relances" and "## Sessions"
# headings, whatever the exit code of claude: claude -p exits 0 even when a tool
# it needed was refused.
set -u
cd "$(dirname "$0")/.." || exit 1
day=${PACHAPLAN_TODAY:-$(date +%F)}
export PACHAPLAN_TODAY=$day
note=reports/note-$day.md
log=reports/run-$day.json

if [ -e "$note" ]; then
  # An old note would pass the checks below without claude writing anything.
  echo "monday note $day: $note already exists, nothing done" >&2
  exit 1
fi
mkdir -p reports

# dontAsk refuses every tool call that no rule allows. Allowed here: the relances
# skill (whose script its allowed-tools pre-approves), the sessions report and the
# note itself. A path rule on Write never matches: file writes are Edit rules.
claude -p "Prépare la note du lundi pour le service planification. Écris-la dans $note avec deux sections, dans cet ordre, sous ces titres exacts : « ## Relances », les relances de la semaine (skill relances) ; « ## Sessions », les sessions des 30 prochains jours remplies à moins de 50 % (\`uv run pachaplan sessions --below 50\`)." \
  --permission-mode dontAsk \
  --allowedTools "Skill(relances)" "Bash(uv run pachaplan sessions --below 50)" "Edit(./$note)" \
  --max-turns 10 \
  --output-format json < /dev/null > "$log"
status=$?
run=$(jq -r '"\(.subtype), \(.num_turns) turns, \(.permission_denials | length) refused"' "$log" 2>/dev/null)

if [ ! -f "$note" ]; then
  echo "monday note $day: $note was not written (claude exit $status, $run)" >&2
  exit 1
fi
for heading in "## Relances" "## Sessions"; do
  if ! grep -qxF "$heading" "$note"; then
    echo "monday note $day: $note has no \"$heading\" heading (claude exit $status, $run)" >&2
    exit 1
  fi
done
echo "monday note $day: done ($run)"
