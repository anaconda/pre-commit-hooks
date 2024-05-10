import subprocess
from textwrap import dedent
from typing import NamedTuple

import cog


class MakefileTarget(NamedTuple):
    target: str
    description: str


def main():
    raw_text = dedent(subprocess.check_output("make", text=True))

    makefile_targets = []
    for line in raw_text.splitlines():
        target, _, description = line.partition(" ")
        makefile_targets.append(
            MakefileTarget(target=target.strip(), description=description.strip())
        )

    max_target_len = max(len(t.target) for t in makefile_targets)
    max_description_len = max(len(t.description) for t in makefile_targets)

    cog.outl(
        "<!-- THE FOLLOWING CODE IS GENERATED BY COG VIA PRE-COMMIT. ANY MANUAL CHANGES WILL BE LOST. -->"
    )
    cog.outl(
        f"| {'Target':{max_target_len + 2}s} | {'Description':{max_description_len}s} |"
    )
    cog.outl(
        f"|{'-'*(max_target_len + 4)}|{'-'*(max_description_len + 2):{max_description_len}s}|"
    )
    for t in makefile_targets:
        cog.outl(
            f"| {'`' + t.target + '`':{max_target_len + 2}s} | {t.description:{max_description_len}s} |"
        )


if __name__ == "__main__":
    # If we run this file as a script, we just make `cog.outl` emit print statements for debugging purposes.
    cog.outl = print
    main()
