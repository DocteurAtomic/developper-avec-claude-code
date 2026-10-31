#!/usr/bin/env bash
# Checks the module 12 exercise, locally, before the workflow runs on GitHub.
#
#   bash <(git show origin/course:exercises/module_12/check.sh) [workflow] [tag]
#
# Run it from the root of the project, on your exercise-12 branch, with a tag that
# exists locally (default: the latest v* tag). It reads the workflow
# (default .github/workflows/release-notes.yml) and runs its steps the way the runner
# would, without GitHub: the guard step with an empty and a set token, the step that
# runs claude -p with a fake claude (a run that exits 0 after a refused tool must
# fail the step), then once for real, with your own Claude login, on the tag. The
# real run is one claude -p session. Nothing is pushed, nothing is published.
set -u
WF=${1:-.github/workflows/release-notes.yml}
TAG=${2:-$(git tag --list 'v*' --sort=-creatordate | head -n 1)}
failed=0
ok()   { printf 'OK    %s\n' "$1"; }
fail() { printf 'FAIL  %s\n' "$1"; failed=$((failed + 1)); }

if [ ! -f "$WF" ]; then echo "No workflow at $WF." >&2; exit 2; fi
if [ -z "$TAG" ] || ! git rev-parse -q --verify "refs/tags/$TAG" > /dev/null; then
    echo "No local tag to try (git tag v0.1 <commit>, or pass one)." >&2; exit 2
fi
work=$(mktemp -d)
trap 'git worktree remove --force "$work/tree" > /dev/null 2>&1; rm -rf "$work"' EXIT

# Splits the workflow into one script per step: guard.sh, claude.sh and their env.
uv run --quiet --no-project --with pyyaml python3 - "$WF" "$work" "$TAG" <<'PY' || exit 2
import json, re, sys, yaml
wf, out, tag = sys.argv[1:]
doc = yaml.safe_load(open(wf, encoding="utf-8"))
on = doc.get("on", doc.get(True, {})) or {}
info = {"tags": bool(isinstance(on, dict) and (on.get("push") or {}).get("tags"))}
steps = [s for job in (doc.get("jobs") or {}).values() for s in job.get("steps", [])]
def env_of(step):
    env = {}
    for k, v in (step.get("env") or {}).items():
        v = str(v)
        if "secrets." in v:
            env[k] = None                      # a secret: set by the check itself
        else:
            env[k] = re.sub(r"\$\{\{\s*github\.ref_name\s*\}\}", tag, v)
    return env
claude = next((i for i, s in enumerate(steps) if "claude -p" in str(s.get("run", ""))), None)
guard = next((i for i, s in enumerate(steps[: claude or 0])
              if "CLAUDE_CODE_OAUTH_TOKEN" in (s.get("env") or {}) and s.get("run")), None)
info["claude"] = claude is not None
info["guard"] = guard is not None
for name, i in (("guard", guard), ("claude", claude)):
    if i is not None:
        run = str(steps[i]["run"])
        info[name + "_expr"] = bool(re.search(r"\$\{\{", run))
        open(f"{out}/{name}.sh", "w").write(run)
        json.dump(env_of(steps[i]), open(f"{out}/{name}.env.json", "w"))
        info[name + "_run"] = run
json.dump(info, open(f"{out}/info.json", "w"))
PY
info=$work/info.json
j() { jq -r "$1" "$info"; }

[ "$(j .tags)" = true ] && ok "the workflow runs on a pushed tag" \
    || fail "the workflow does not run on: push: tags"
[ "$(j .claude)" = true ] || { fail "no step runs claude -p"; echo "$failed check(s) failed."; exit 1; }
[ "$(j .guard)" = true ] || fail "no step before claude -p checks CLAUDE_CODE_OAUTH_TOKEN"
claude_run=$(j .claude_run)
grep -q -- '--permission-mode dontAsk' <<< "$claude_run" && ok "claude -p runs in dontAsk" \
    || fail "claude -p does not run with --permission-mode dontAsk"
grep -q -- '--max-turns' <<< "$claude_run" && ok "claude -p has a turn limit" \
    || fail "claude -p has no --max-turns"
if grep -qE -- 'bypassPermissions|dangerously-skip-permissions' <<< "$claude_run"; then
    fail "claude -p skips the permission checks"
fi
for s in guard claude; do
    [ "$(j ".${s}_expr // false")" = true ] && fail "the $s step has \${{ }} in its run: pass values through env"
done

# run_step NAME TOKEN [PATH-PREFIX]: runs a step script in the worktree, with its env.
git worktree add -q --detach "$work/tree" "$TAG" || exit 2
run_step() {
    local name=$1 token=$2 prefix=${3:-}
    ( cd "$work/tree" || exit 2
      while IFS=$'\t' read -r k v; do
          if [ "$v" = "null" ]; then
              if [ "$k" = CLAUDE_CODE_OAUTH_TOKEN ] && [ -n "$token" ]; then export "$k=$token"; else unset "$k"; fi
          else export "$k=$v"; fi
      done < <(jq -r 'to_entries[] | "\(.key)\t\(.value)"' "$work/$name.env.json")
      [ -n "$prefix" ] && export PATH="$prefix:$PATH"
      export GITHUB_OUTPUT=$work/out GITHUB_PATH=$work/path GITHUB_STEP_SUMMARY=$work/summary
      bash -e "$work/$name.sh" ) > "$work/$name.log" 2>&1
}

if [ "$(j .guard)" = true ]; then
    if run_step guard ""; then fail "the guard passes with an empty token"
    else ok "the guard fails with an empty token"; fi
    if run_step guard "dummy-token"; then ok "the guard passes with a token"
    else fail "the guard fails even with a token: $(tail -1 "$work/guard.log")"; fi
fi

# A fake claude that exits 0 after a refused tool, like a dontAsk run that could not work.
mkdir -p "$work/fake"
cat > "$work/fake/claude" <<'FAKE'
#!/usr/bin/env bash
cat <<'JSON'
{"type":"result","subtype":"success","is_error":false,"num_turns":3,"result":"I could not read the commits: the command was refused.","permission_denials":[{"tool_name":"Bash","tool_input":{"command":"git log"}}]}
JSON
FAKE
chmod +x "$work/fake/claude"
if run_step claude "" "$work/fake"; then
    fail "the claude step passes when claude exits 0 after a refused tool"
else
    ok "the claude step fails when claude exits 0 after a refused tool"
fi

rm -f "$work/tree/notes.md"
echo "Running the claude step for real on $TAG (one claude -p session)..."
if run_step claude ""; then
    if [ -s "$work/tree/notes.md" ]; then
        ok "the real run on $TAG writes notes.md"
        cp "$work/tree/notes.md" "notes-$TAG.md"
    else
        fail "the real run exits 0 but notes.md is missing or empty"
    fi
else
    fail "the real run fails: $(tail -3 "$work/claude.log")"
fi

if [ "$failed" -eq 0 ]; then echo "All checks passed. The notes are in notes-$TAG.md."; exit 0; fi
echo "$failed check(s) failed."; exit 1
