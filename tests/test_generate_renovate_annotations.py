import json
import subprocess
from pathlib import Path
from textwrap import dedent

import pytest
import yaml
from anaconda_pre_commit_hooks.add_renovate_annotations import (
    Dependencies,
    Dependency,
    add_comments_to_env_file,
    load_dependencies,
    parse_pip_index_overrides,
    setup_conda_environment,
)

DEFAULT_FILES_REGEX_STRING = r"environment.*\.ya?ml"

ENVIRONMENT_YAML = dedent("""\
    channels:
    - defaults
    dependencies:
    - python=3.10
    # renovate: comment to be overridden
    - pytest
    - pip
    - pip:
      - private-package
      - fastapi==0.110.0
      - click[extras]
      - -e .
    name: some-environment-name
""")


@pytest.fixture()
def repo_root() -> Path:
    return Path(__file__).parents[1]


def test_ensure_default_files_regex_in_pre_commit_hooks_yaml_matches_tested(repo_root):
    pre_commit_hooks_path = repo_root / ".pre-commit-hooks.yaml"
    hooks = yaml.safe_load(pre_commit_hooks_path.read_text())

    hook_map = {h["id"]: h for h in hooks}
    hook_spec = hook_map["generate-renovate-annotations"]
    files_regex = hook_spec["files"]

    assert files_regex == DEFAULT_FILES_REGEX_STRING


@pytest.fixture()
def environment_yaml():
    return yaml.safe_load(ENVIRONMENT_YAML)


def test_load_environment_yaml(environment_yaml):
    assert environment_yaml == {
        "channels": ["defaults"],
        "dependencies": [
            "python=3.10",
            "pytest",
            "pip",
            {"pip": ["private-package", "fastapi==0.110.0", "click[extras]", "-e ."]},
        ],
        "name": "some-environment-name",
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


@pytest.mark.usefixtures("mock_subprocess_run")
def test_add_comments_to_env_file(tmp_path):
    env_file_path = tmp_path / "environment.yml"
    with env_file_path.open("w") as fp:
        fp.write(ENVIRONMENT_YAML)

    # Modify the file in-place
    add_comments_to_env_file(
        env_file_path,
        load_dependencies(),
        pip_index_overrides={"private-package": "https://private-index.com/simple"},
    )

    with env_file_path.open("r") as fp:
        new_contents = fp.read()

    # Compare the results. Versions and channels should come from the mock above.
    assert new_contents == dedent("""\
        channels:
        - defaults
        dependencies:
        # renovate: datasource=conda depName=main/python
        - python=3.10.14
        # renovate: datasource=conda depName=main/pytest
        - pytest
        # renovate: datasource=conda depName=main/pip
        - pip
        - pip:
          # renovate: datasource=pypi registryUrl=https://private-index.com/simple
          - private-package
          # renovate: datasource=pypi
          - fastapi==0.110.0
          # renovate: datasource=pypi
          - click[extras]==8.1.7
          - -e .
        name: some-environment-name
    """)
