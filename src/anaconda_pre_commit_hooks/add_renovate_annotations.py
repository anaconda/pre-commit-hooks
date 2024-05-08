#!/usr/bin/env python3
"""Automagically add renovate comments to conda environment files.

Given a number of paths specified as CLI arguments, we extract the unique app directories
and then add comments to all environment files in those directories. This prevents running
the environment update for each file. In generall, pre-commit will pass this file list in
based on its own include rules specified in .pre-commit-config.yaml.

"""
import contextlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import NamedTuple, Optional, TypedDict
import typer

INTERNAL_PYPI_PACKAGES = {}
INTERNAL_PYPI_INDEX = ""

CondaOrPip = str
PackageName = str
PackageVersion = str
ChannelName = str
ChannelOverrides = dict[PackageName, ChannelName]


class Dependency(TypedDict):
    name: str
    channel: str
    version: str


class Dependencies(NamedTuple):
    pip: dict[str, Dependency]
    conda: dict[str, Dependency]


@contextlib.contextmanager
def working_dir(d: Path):
    orig = Path.cwd()
    os.chdir(d)
    yield
    os.chdir(orig)


def load_dependencies(project_directory: Path) -> Dependencies:
    with working_dir(project_directory):
        # First ensure the conda environment exists
        result = subprocess.run(["make", "setup"], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to run make setup for {project_directory}")
            print(result.stdout)
            print(result.stderr)
            result.check_returncode()
        result = subprocess.run(
            ["conda", "list", "-p", "./env", "--json"], capture_output=True, text=True
        )
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
            result.check_returncode()
        data = json.loads(result.stdout)
        pip_deps = {
            x["name"]: Dependency(
                name=x["name"], channel=x["channel"], version=x["version"]
            )
            for x in data
            if x["channel"] == "pypi"
        }

        # We use endswith to match both pkgs/main and repo/main to main
        conda_deps = {
            x["name"]: Dependency(
                name=x["name"],
                channel="main" if x["channel"].endswith("/main") else x["channel"],
                version=x["version"],
            )
            for x in data
            if x["channel"] != "pypi"
        }
        if len(pip_deps) + len(conda_deps) != len(data):
            raise ValueError("Mismatch parsing dependencies")
        return Dependencies(pip=pip_deps, conda=conda_deps)


def process_environment_file(
    env_file: Path,
    dependencies: Dependencies,
    conda_channel_overrides: Optional[ChannelOverrides] = None,
):
    """Process an environment file, which entails adding renovate comments and pinning the installed version."""
    conda_channel_overrides = conda_channel_overrides or {}
    with env_file.open() as fp:
        in_lines = fp.readlines()

    out_lines = []
    in_dependencies = False
    in_pip_dependencies = False
    for raw_line in in_lines:
        line = raw_line.strip()
        if line == "dependencies:":
            in_dependencies = True
        elif in_dependencies and not (line.startswith("#") or line.startswith("-")):
            in_dependencies = False
        elif line == "- pip:":
            in_pip_dependencies = True

        if in_dependencies and line.startswith("-") and not line.endswith(":"):
            # It's a dependency spec
            m = re.search(r"-\s*([\w\-\[\],.]+)", line)
            if m is None:
                raise ValueError(f"Could not parse line: {line}")
            package_name_with_extras = m.group(1).lower().replace("_", "-")
            if package_name_with_extras.startswith(
                "."
            ) or package_name_with_extras.startswith("-e"):
                package_name = "."
            else:
                m = re.search(r"([\w-]+)", package_name_with_extras)
                if m is None:
                    raise ValueError(
                        f"Could not parse package: {package_name_with_extras}"
                    )
                package_name = m.group(1)

            matching_dependency: Optional[Dependency] = (
                dependencies.pip.get(package_name)
                if in_pip_dependencies
                else dependencies.conda.get(package_name)
            )
            if in_pip_dependencies:
                datasource, dep_name = "pypi", package_name
            else:
                channel_name = "main"
                if package_name in conda_channel_overrides:
                    channel_name = conda_channel_overrides[package_name]
                elif matching_dependency:
                    channel_name = matching_dependency["channel"]
                datasource, dep_name = "conda", f"{channel_name}/{package_name}"

            indentation = len(raw_line.rstrip()) - len(line)
            if out_lines[-1].strip().startswith("# renovate"):
                out_lines.pop(-1)
            if package_name != ".":
                if datasource == "conda":
                    renovate_line = f"{' ' * indentation}# renovate: datasource={datasource} depName={dep_name}\n"
                elif dep_name in INTERNAL_PYPI_PACKAGES:
                    renovate_line = f"{' ' * indentation}# renovate: datasource={datasource} registryUrl={INTERNAL_PYPI_INDEX}\n"
                else:
                    renovate_line = (
                        f"{' ' * indentation}# renovate: datasource={datasource}\n"
                    )
                out_lines.append(renovate_line)

            # Attempt to load the actual version from the dependencies dictionary to write to the file
            if matching_dependency:
                versioned_line = None
                if datasource == "conda":
                    versioned_line = f"{' ' * indentation}- {package_name}={matching_dependency['version']}\n"
                else:
                    versioned_line = f"{' ' * indentation}- {package_name_with_extras}=={matching_dependency['version']}\n"
                out_lines.append(versioned_line)
            else:
                out_lines.append(raw_line)
        else:
            out_lines.append(raw_line)

    # Overwrite the file now
    with env_file.open("w") as fp:
        fp.writelines(out_lines)


def add_comments_to_env_files(
    env_files: list[Path],
    dependencies: Dependencies,
    conda_channel_overrides: Optional[ChannelOverrides] = None,
) -> None:
    """Process each environment file found."""
    for f in env_files:
        process_environment_file(f, dependencies, conda_channel_overrides=conda_channel_overrides)


def cli(env_files: list[Path]) -> None:

    # Group into a list of parent directories. This prevents us from running
    # `make setup` for each file, and only once per project.
    project_dirs = sorted({env_file.parent for env_file in env_files})

    for project_dir in project_dirs:
        deps = load_dependencies(project_dir)
        project_env_files = [e for e in env_files if e.parent == project_dir]
        add_comments_to_env_files(project_env_files, deps)


def main() -> None:
    typer.run(cli)


if __name__ == "__main__":
    main()
