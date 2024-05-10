import shlex
import subprocess

import cog

OUTPUT_STR_FORMAT = """\
```{language}
{text}
```\
"""


def main(command: str, language: str = "shell"):
    """Run a command in a subprocess and send the resulting output to cog's output, wrapped in a shell code block."""
    raw_text = subprocess.check_output(shlex.split(command), text=True)
    output = OUTPUT_STR_FORMAT.format(language=language, text=raw_text.strip())
    for line in output.splitlines():
        cog.outl(line.rstrip())
