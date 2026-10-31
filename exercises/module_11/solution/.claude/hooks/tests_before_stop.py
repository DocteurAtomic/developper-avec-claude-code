"""Stop hook: send Claude back to work while the test suite fails.

The suite runs as the CI runs it, with PACHAPLAN_DB set and --fail-on-skip: without
the variable, the integration tests are skipped and a red integration test would pass.
When stop_hook_active is true, Claude is already continuing because of this hook:
let it stop, so that a failure it cannot fix does not loop.
"""

import json
import os
import subprocess
import sys


def main() -> int:
    event = json.load(sys.stdin)
    if event.get("stop_hook_active"):
        return 0
    project = os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or "."
    env = dict(os.environ, PACHAPLAN_DB="data/pachaplan.sqlite")
    run = subprocess.run(
        ["uv", "run", "pytest", "-q", "--fail-on-skip"],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
    )
    if run.returncode == 0:
        return 0
    tail = "\n".join(run.stdout.strip().splitlines()[-15:])
    print(f"The test suite fails, fix it before you stop:\n{tail}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
