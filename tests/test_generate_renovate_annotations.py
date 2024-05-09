from textwrap import dedent

import pytest
import yaml

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


def test_the_tests():
    assert True


def test_load_environment_yaml(environment_yaml):
    assert environment_yaml == {
        "channels": ["defaults"],
        "dependencies": ["python=3.10", "pytest", "pip", {"pip": ["-e ."]}],
    }
