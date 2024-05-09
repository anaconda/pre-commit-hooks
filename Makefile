SHELL := /bin/bash -o pipefail -o errexit

# Conda-related paths
conda_env_dir := ./env
conda_env_file := environment-dev.yml

# Commands
CONDA_EXE ?= conda
conda_run := $(CONDA_EXE) run --live-stream --prefix $(conda_env_dir)

help:  ## Display help on all Makefile targets
	@fgrep -h "##" $(MAKEFILE_LIST) \
		| fgrep -v fgrep \
		| fgrep -v 'sed -e' \
		| sed -e 's/\\$$//' \
		| sed -e 's/##//' \
		| awk -F ':' '{ printf "%-15s %s\n", $$1, $$2 }'

setup:  ## Setup local conda environment for development
	$(CONDA_EXE) env \
		$(shell [ -d $(conda_env_dir) ] && echo update || echo create) \
		--prefix $(conda_env_dir) \
		--file $(conda_env_file)

install-hooks:  ## Download + install all pre-commit hooks
	pre-commit install-hooks

pre-commit:  ## Run pre-commit against all files
	pre-commit run --verbose --show-diff-on-failure --color=always --all-files

type-check:  ## Run static type checks
	$(conda_run) mypy

test:  ## Run all the unit tests
	$(conda_run) pytest

.PHONY: $(MAKECMDGOALS)
