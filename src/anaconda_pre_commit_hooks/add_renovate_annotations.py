"""Automagically add renovate comments to conda environment files.

Given a number of paths specified as CLI arguments, we extract the unique app directories
and then add comments to all environment files in those directories. This prevents running
the environment update for each file. In general, pre-commit will pass this file list in
based on its own include rules specified in .pre-commit-config.yaml.

"""

import json
import re
import shlex
import subprocess
from pathlib import Path
from typing import Annotated, NamedTuple, Optional, TypedDict

import typer

CondaOrPip = str
PackageName = str
PackageVersion = str
ChannelName = str
IndexUrl = str
ChannelOverrides = dict[PackageName, ChannelName]
IndexOverrides = dict[PackageName, IndexUrl]


class Dependency(TypedDict):
    name: str
    channel: str
    version: str


class Dependencies(NamedTuple):
    pip: dict[str, Dependency]
    conda: dict[str, Dependency]


def setup_conda_environment(command: str, *, cwd: Optional[Path] = None) -> None:
    """Ensure the conda environment is setup and updated."""
    cwd = cwd or Path.cwd()
    result = subprocess.run(
        shlex.split(command), capture_output=True, text=True, cwd=cwd
    )
    if result.returncode != 0:
        print(f"Failed to run setup command in {cwd}")
        print(result.stdout)
        print(result.stderr)
        result.check_returncode()


def list_packages_in_conda_environment(environment_selector: str) -> list[dict]:
    # Then we list the actual versions of each package in the environment
    result = subprocess.run(
        ["conda", "list", *shlex.split(environment_selector), "--json"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        result.check_returncode()

    return json.loads(result.stdout)


def load_dependencies(
    project_directory: Optional[Path] = None,
    create_command: str = "make setup",
    environment_selector: str = "-p ./env",
) -> Dependencies:
    """Load the dependencies from a live conda environment.

    Args:
        project_directory: The directory in which the project is located.
        create_command: A command used to create a new conda environment from the environment file(s).
        environment_selector: A string used to select the environment (-p ./env or -n name for a named environment).

    Returns:
        An object containing all dependencies in the installed environment, split between conda and pip packages.

    """
    setup_conda_environment(create_command, cwd=project_directory or Path.cwd())

    data = list_packages_in_conda_environment(environment_selector)

    # We split the list separately into pip & conda dependencies
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


def add_comments_to_env_file(
    env_file: Path,
    dependencies: Dependencies,
    *,
    conda_channel_overrides: Optional[ChannelOverrides] = None,
    pip_index_overrides: Optional[IndexOverrides] = None,
) -> None:
    """Process an environment file, which entails adding renovate comments and pinning the installed version."""
    conda_channel_overrides = conda_channel_overrides or {}
    pip_index_overrides = pip_index_overrides or {}

    with env_file.open() as fp:
        in_lines = fp.readlines()

    out_lines: list[str] = []
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
                elif (index_url := pip_index_overrides.get(dep_name)) is not None:
                    renovate_line = f"{' ' * indentation}# renovate: datasource={datasource} registryUrl={index_url}\n"
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


def parse_pip_index_overrides(
    internal_pip_index_url: str, internal_pip_package: list[str]
) -> dict[PackageName, IndexUrl]:
    pip_index_overrides = {}
    if internal_pip_index_url and internal_pip_package:
        for pkg_name in internal_pip_package:
            pip_index_overrides[pkg_name] = internal_pip_index_url
    return pip_index_overrides


def cli(
    env_files: list[Path],
    internal_pip_package: Annotated[Optional[list[str]], typer.Option()] = None,
    internal_pip_index_url: Annotated[str, typer.Option()] = "",
) -> None:
    # Construct a mapping of package name to index URL based on CLI options
    pip_index_overrides = parse_pip_index_overrides(
        internal_pip_index_url, internal_pip_package or []
    )

    # Group into a list of parent directories. This prevents us from running
    # `make setup` for each file, and only once per project.
    project_dirs = sorted({env_file.parent for env_file in env_files})
    for project_dir in project_dirs:
        deps = load_dependencies(project_dir)
        project_env_files = (e for e in env_files if e.parent == project_dir)
        for env_file in project_env_files:
            add_comments_to_env_file(
                env_file, deps, pip_index_overrides=pip_index_overrides
            )


def main() -> None:
    typer.run(cli)


if __name__ == "__main__":
    main()
