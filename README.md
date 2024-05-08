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
  rev: main
  hooks:
    - id: generate-renovate-annotations
      args: [
      --internal-pip-index-url=https://pypi.anaconda.org/my-organization/simple,
      --internal-pip-package=my-private-package,
      --internal-pip-package=my-other-private-package,
    ]
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
