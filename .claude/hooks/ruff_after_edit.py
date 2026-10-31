"""PostToolUse hook on Edit and Write: ruff format, then ruff check, on the edited file.

Claude Code sends the tool call as JSON on stdin. Files that are not Python are left
alone. When ruff check still finds an error after formatting, its report goes to stderr
and the hook exits 2: that is the only exit code whose stderr Claude reads after a tool
has run. Any other failure of the hook itself is reported and exits 1, which does not
interrupt the session.
"""

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    event = json.load(sys.stdin)
    path = Path(event.get("tool_input", {}).get("file_path", ""))
    if path.suffix != ".py" or not path.is_file():
        return 0
    subprocess.run(["ruff", "format", "--quiet", str(path)], check=False)
    check = subprocess.run(
        ["ruff", "check", "--output-format", "concise", str(path)],
        capture_output=True,
        text=True,
    )
    if check.returncode == 0:
        return 0
    if check.returncode == 1:
        print(check.stdout.strip(), file=sys.stderr)
        print("Fix these ruff errors in the file you just edited.", file=sys.stderr)
        return 2
    print(check.stderr.strip() or "ruff could not run", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
