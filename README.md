[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/mattkram/mjml-hook/main.svg)](https://results.pre-commit.ci/latest/github/mattkram/mjml-hook/main)

# Anaconda pre-commit hooks

This repo contains custom `pre-commit` hooks.

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
