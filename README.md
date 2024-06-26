# Anaconda pre-commit hooks

This repo contains custom `pre-commit` hooks.

## generate-renovate-annotations

The `generate-renovate-annotations` hook is used to add Renovate comments to conda environment files.
The format of these comments is prescribed with a RegEx rule, with more details in the [.documentation](https://github.com/anaconda/renovate-config/blob/main/docs/conda-environment.md)

By default, this hook will work for all files matching the `environment.*\.ya?ml` regular expression.
This matches common formats like `environment.yaml`, `environment.yml`, and `environment-suffix.yml`.

To pull pip packages from an alternate index, each package must be specified with the `--internal-pip-package` option (multiple allowed).
The index URL is specified with the `--internal-pip-index-url` option.

> **Note:** The Renovate worker must be configured with adequate credentials if this URL requires authentication.

An example usage is shown below:

```yaml
- repo: https://github.com/anaconda/pre-commit-hooks
  rev: main  # Use the ref you want to point at
  hooks:
    - id: generate-renovate-annotations
      args: [
      --internal-pip-index-url=https://pypi.anaconda.org/my-organization/simple,
      --internal-pip-package=my-private-package,
      --internal-pip-package=my-other-private-package,
      --create-command="make setup",     # Default value
      --environment-selector="-p ./env", # Default value
      --disable-environment-creation     # Creation enabled by default
    ]
```

The hook is backed by a CLI command, whose help output is reproduced below:

<!-- [[[cog
#import os, sys; sys.path.insert(0, os.path.join(os.getcwd(), "dev"))
#from generate_cli_output import main
#main(command="generate-renovate-annotations --help")
]]] -->
<!-- [[[end]]] -->
```shell
Usage: generate-renovate-annotations [OPTIONS] ENV_FILES... COMMAND [ARGS]...

 Generate Renovate comments for a list of conda environment files.
 For each file, we:

  • Run a command to ensure the environment is created/updated
  • Extract a list of installed packages in that environment, including pip
  • Generate a Renovate annotation comment, including the package name and
    channel. This step also allows for overriding the index of pip packages.
  • Pin the exact installed version of each dependency.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│ *    env_files      ENV_FILES...  A list of conda environment files,         │
│                                   typically passed in from pre-commit        │
│                                   automatically                              │
│                                   [default: None]                            │
│                                   [required]                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --internal-pip-package                TEXT  One or more packages to pull     │
│                                             from the                         │
│                                             --internal-pip-index-url         │
│                                             [default: None]                  │
│ --internal-pip-index-url              TEXT  An optional extra pip index URL, │
│                                             used in conjunction with the     │
│                                             --internal-pip-package option    │
│ --create-command                      TEXT  A command to invoke at each      │
│                                             parent directory of all          │
│                                             environment files to ensure the  │
│                                             conda environment is created and │
│                                             updated                          │
│                                             [default: make setup]            │
│ --environment-selector                TEXT  A string used to select the      │
│                                             conda environment, either        │
│                                             prefix-based (recommended) or    │
│                                             named                            │
│                                             [default: -p ./env]              │
│ --disable-environment-creation              If set, environment will not be  │
│                                             created/updated before           │
│                                             annotations are added.           │
│ --help                                      Show this message and exit.      │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## run-cog

The `run-cog` hook can be used to run the [`cog`](https://nedbatchelder.com/code/cog) tool automatically to generate code when committing a file.
One common example is to generate command-line output in a README file.

The example below will run `cog` on all text-like files, ensuring the working directory is set to the directory in which the file is located.
This is particularly useful if the `cog` script itself uses `subprocess` to execute command-line applications.

```yaml
-   repo: https://github.com/anaconda/pre-commit-hooks
    rev: main  # Use the ref you want to point at
    hooks:
    -   id: run-cog
        args: ["--working-directory-level", "-1"]
```
## mjml-hook

A simple wrapper around the [`mjml`](https://github.com/mjmlio/mjml) tool to use as a [`pre-commit`](https://pre-commit.com) hook.

### Using mjml-hook with pre-commit

Add this to your `.pre-commit-config.yaml`

```yaml
-   repo: https://github.com/mattkram/mjml-hook
    rev: main  # Use the ref you want to point at
    hooks:
    -   id: mjml
```

### What does the hook do?

The pre-commit hook will execute any time a file with the pattern `*.mjml` is staged for commit.
For each of these files, the following command is run:

```shell
mjml <filename>.mjml -o <filename>.html
```

where the base filename remains the same, and the extension is changed.

If the HTML file is already being tracked by `git` and is changed by the hook, `pre-commit` will raise an error.
If this is a new template, `pre-commit` will not fail and you may need to do an amend commit to add the initial HTML file to the `git` history.

```shell
git commit --amend path/to/file.html
```

## Dev setup

We have a dev setup that uses `conda` for environment management.
We also use `make` to automate common tasks.
The targets are documented below:


<!-- [[[cog
import os, sys; sys.path.insert(0, os.path.join(os.getcwd(), "dev"))
from generate_makefile_targets_table import main; main()
]]] -->
<!-- THE FOLLOWING CODE IS GENERATED BY COG VIA PRE-COMMIT. ANY MANUAL CHANGES WILL BE LOST. -->
| Target          | Description                                                              |
|-----------------|--------------------------------------------------------------------------|
| `help`          | Display help on all Makefile targets                                     |
| `setup`         | Setup local conda environment for development                            |
| `install-hooks` | Download + install all pre-commit hooks                                  |
| `pre-commit`    | Run pre-commit against all files                                         |
| `type-check`    | Run static type checks                                                   |
| `test`          | Run all the unit tests                                                   |
| `cog-readme`    | Run cog on the README.md to generate command output                      |
<!-- [[[end]]] -->

> **Note:** Interestingly, the table above is generated by the `cog` hook defined in this repo :smile:
