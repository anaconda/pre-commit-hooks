from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Sequence


def run_cog(
    filenames: Sequence[str],
    working_directory_level: int,
) -> int:
    """Execute cog in a subprocess on a sequence of files in rewrite mode.

    We wrap cog with a subprocess call so that we can optionally remove parts of the
    path, which makes it easier to work within a mono-repo.

    Args:
        filenames: A list of filenames, passed in from pre-commit.
        working_directory_level: The number of levels from the repo root to traverse
            into when setting cog's working directory. This is useful if cog needs to
            execute a subprocess within a certain subdirectory. This number will be the
            number of path elements from the repo root to include in cog's working
            directory. A value of 0 indicates cog will run from the repo root. A value
            of -1 indicates that cog should run from the parent directory of the file
            being processed.

    """

    for filename in filenames:
        file_path = Path(filename)
        if working_directory_level == 0:
            cwd = Path.cwd()
        elif working_directory_level == -1:
            cwd = file_path.parent
        else:
            path_str = file_path.as_posix()
            elements = path_str.split("/")
            cwd = Path(*elements[:working_directory_level])

        result = subprocess.run(["cog", "-r", file_path.name], cwd=str(cwd))
        if result.returncode != 0:
            return result.returncode

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'filenames', nargs='*',
        help='Filenames pre-commit believes are changed.',
    )
    parser.add_argument(
        '--working-directory-level',
        default=0,
        type=int,
        help="The number of levels from the repo root to traverse into when setting cog's working directory."
    )
    args = parser.parse_args(argv)

    return run_cog(
        args.filenames,
        args.working_directory_level,
    )


if __name__ == '__main__':
    raise SystemExit(main())
