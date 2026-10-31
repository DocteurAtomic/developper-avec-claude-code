"""PreToolUse hook on Bash: refuse git push, whatever the options before "push".

The deny rule Bash(git push:*) in settings.json already refuses the plain form; this
hook also catches "git -C . push" and "cd x && git push", and tells Claude why.
"""

import json
import re
import sys

PUSH = re.compile(r"\bgit\b[^;&|\n]*\bpush\b")


def main() -> int:
    event = json.load(sys.stdin)
    command = event.get("tool_input", {}).get("command", "")
    if PUSH.search(command):
        print(
            "git push is refused in this project: commit, report what you did, "
            "and leave the push to the developer after review.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
