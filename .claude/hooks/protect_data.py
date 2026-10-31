"""PreToolUse hook on Edit and Write: refuse any write under data/.

data/pachaplan.sqlite is the planning data; nothing under data/ is edited by hand.
The hook only sees Claude's file tools: a write made by a Bash command, a script or
a test does not go through it.
"""

import json
import os
import sys
from pathlib import Path


def main() -> int:
    event = json.load(sys.stdin)
    target = event.get("tool_input", {}).get("file_path", "")
    if not target:
        return 0
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or ".")
    path = Path(event.get("cwd") or project, target).resolve()
    if path.is_relative_to((project / "data").resolve()):
        print(
            f"{target} is under data/, which is never written. "
            "Work on a copy outside data/ and pass it with --db.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
