SHELL := /bin/bash -o pipefail -o errexit

help:
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

install-hooks:  ## Download + install all pre-commit hooks
	pre-commit install-hooks

pre-commit:  ## Run pre-commit against all files
	pre-commit run --verbose --show-diff-on-failure --color=always --all-files

.PHONY: all $(MAKECMDGOALS)
