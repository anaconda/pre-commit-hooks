import json
import subprocess
from pathlib import Path
from textwrap import dedent

import pytest
import yaml
from anaconda_pre_commit_hooks.add_renovate_annotations import (
    Dependencies,
    Dependency,
    load_dependencies,
    parse_pip_index_overrides,
    setup_conda_environment,
)

ENVIRONMENT_YAML = dedent("""\
    channels:
    - defaults
    dependencies:
    - python=3.10
    - pytest
    - pip
    - pip:
      - -e .
""")


@pytest.fixture()
def environment_yaml():
    return yaml.safe_load(ENVIRONMENT_YAML)


def test_load_environment_yaml(environment_yaml):
    assert environment_yaml == {
        "channels": ["defaults"],
        "dependencies": ["python=3.10", "pytest", "pip", {"pip": ["-e ."]}],
    }


@pytest.mark.parametrize(
    "index_url, packages, expect_empty",
    [
        ("https://my-internal-index.com/simple", ["package-1", "package-2"], False),
        ("", ["package-1", "package-2"], True),
        ("https://my-internal-index.com/simple", [], True),
        ("", [], True),
    ],
)
def test_parse_pip_index_overrides(index_url, packages, expect_empty):
    """Test parsing of CLI arguments into a mapping.

    The mapping is empty of either of the arguments are Falsy.

    """
    result = parse_pip_index_overrides(index_url, packages)
    if expect_empty:
        assert result == {}
    else:
        assert result == {p: index_url for p in packages}


@pytest.fixture()
def mock_subprocess_run(monkeypatch):
    old_subprocess_run = subprocess.run

    def f(args, *posargs, **kwargs):
        if args == ["make", "setup"]:
            return subprocess.CompletedProcess(
                args,
                0,
                "",
                "",
            )
        elif args[:2] == ["conda", "list"]:
            return subprocess.CompletedProcess(
                args,
                0,
                json.dumps(
                    [
                        {
                            "base_url": "https://conda.anaconda.org/pypi",
                            "build_number": 0,
                            "build_string": "pypi_0",
                            "channel": "pypi",
                            "dist_name": "click-8.1.7-pypi_0",
                            "name": "click",
                            "platform": "pypi",
                            "version": "8.1.7",
                        },
                        {
                            "base_url": "https://repo.anaconda.com/pkgs/main",
                            "build_number": 1,
                            "build_string": "hb885b13_1",
                            "channel": "pkgs/main",
                            "dist_name": "python-3.10.14-hb885b13_1",
                            "name": "python",
                            "platform": "osx-arm64",
                            "version": "3.10.14",
                        },
                    ]
                ),
                "",
            )
        else:
            return old_subprocess_run(args, *posargs, **kwargs)  # pragma: nocover

    monkeypatch.setattr(subprocess, "run", f)


@pytest.mark.usefixtures("mock_subprocess_run")
def test_setup_conda_environment():
    result = setup_conda_environment("make setup")
    assert result is None


@pytest.mark.usefixtures("mock_subprocess_run")
def test_load_dependencies():
    dependencies = load_dependencies(Path.cwd())
    assert dependencies == Dependencies(
        pip={"click": Dependency(name="click", channel="pypi", version="8.1.7")},
        conda={"python": Dependency(name="python", channel="main", version="3.10.14")},
    )
