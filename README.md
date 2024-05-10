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
import os, sys; sys.path.insert(0, os.path.join(os.getcwd(), "dev"))
from generate_cli_output import main
main(command="generate-renovate-annotations --help")
]]] -->
```shell
[1m                                                                                [0m
[1m [0m[1;33mUsage: [0m[1mgenerate-renovate-annotations [OPTIONS] ENV_FILES... COMMAND [ARGS]...[0m[1m [0m[1m [0m
[1m                                                                                [0m
 Generate Renovate comments for a list of [1;36;40mconda[0m environment files.
 [2mFor each file, we:[0m

 [1;33m • [0m[2mRun a command to ensure the environment is created/updated[0m[2m                 [0m
 [1;33m • [0m[2mExtract a list of installed packages in that environment, including pip[0m[2m    [0m
 [1;33m • [0m[2mGenerate a Renovate annotation comment, including the package name and [0m[2m    [0m
 [1;33m   [0m[2mchannel.[0m[2m [0m[2mThis step also allows for overriding the index of pip packages.[0m[2m   [0m
 [1;33m • [0m[2mPin the exact installed version of each dependency.[0m[2m                        [0m

[2m╭─[0m[2m Arguments [0m[2m─────────────────────────────────────────────────────────────────[0m[2m─╮[0m
[2m│[0m [31m*[0m    env_files      [1;33mENV_FILES...[0m  A list of conda environment files,         [2m│[0m
[2m│[0m                                   typically passed in from pre-commit        [2m│[0m
[2m│[0m                                   automatically                              [2m│[0m
[2m│[0m                                   [2m[default: None]                           [0m [2m│[0m
[2m│[0m                                   [2;31m[required]                                [0m [2m│[0m
[2m╰──────────────────────────────────────────────────────────────────────────────╯[0m
[2m╭─[0m[2m Options [0m[2m───────────────────────────────────────────────────────────────────[0m[2m─╮[0m
[2m│[0m [1;36m-[0m[1;36m-internal[0m[1;36m-pip-package[0m                [1;33mTEXT[0m  One or more packages to pull     [2m│[0m
[2m│[0m                                             from the                         [2m│[0m
[2m│[0m                                             --internal-pip-index-url         [2m│[0m
[2m│[0m                                             [2m[default: None]                 [0m [2m│[0m
[2m│[0m [1;36m-[0m[1;36m-internal[0m[1;36m-pip-index-url[0m              [1;33mTEXT[0m  An optional extra pip index URL, [2m│[0m
[2m│[0m                                             used in conjunction with the     [2m│[0m
[2m│[0m                                             --internal-pip-package option    [2m│[0m
[2m│[0m [1;36m-[0m[1;36m-create[0m[1;36m-command[0m                      [1;33mTEXT[0m  A command to invoke at each      [2m│[0m
[2m│[0m                                             parent directory of all          [2m│[0m
[2m│[0m                                             environment files to ensure the  [2m│[0m
[2m│[0m                                             conda environment is created and [2m│[0m
[2m│[0m                                             updated                          [2m│[0m
[2m│[0m                                             [2m[default: make setup]           [0m [2m│[0m
[2m│[0m [1;36m-[0m[1;36m-environment[0m[1;36m-selector[0m                [1;33mTEXT[0m  A string used to select the      [2m│[0m
[2m│[0m                                             conda environment, either        [2m│[0m
[2m│[0m                                             prefix-based (recommended) or    [2m│[0m
[2m│[0m                                             named                            [2m│[0m
[2m│[0m                                             [2m[default: -p ./env]             [0m [2m│[0m
[2m│[0m [1;36m-[0m[1;36m-disable[0m[1;36m-environment-creation[0m        [1;33m    [0m  If set, environment will not be  [2m│[0m
[2m│[0m                                             created/updated before           [2m│[0m
[2m│[0m                                             annotations are added.           [2m│[0m
[2m│[0m [1;36m-[0m[1;36m-help[0m                                [1;33m    [0m  Show this message and exit.      [2m│[0m
[2m╰──────────────────────────────────────────────────────────────────────────────╯[0m
```
<!-- [[[end]]] -->

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
