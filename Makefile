# py project metadata
PYPROJECT_NAME?=$(shell awk -F\" '/^name *=/ { print $$2; exit; }' pyproject.toml)
PYPROJECT_VERSION?=$(shell awk -F\" '/^version *=/ { print $$2; exit; }' pyproject.toml)

# poetry (in-project virtual env name is `.venv`)
POETRY?=$(shell command -v poetry 2> /dev/null)
POETRY_RUN?=$(POETRY) run
POETRY_LOCK?=poetry.lock
POETRY_VENV?=.venv
POETRY_VENV_STAMP?=$(POETRY_VENV)/.install.stamp
POETRY_SETUP_COMMAND?=install
ifdef CI
POETRY_OUTPUT_ARGS?=--no-ansi
endif

# release
RELEASE_VERSION?=$(shell \
	if (echo "$(PYPROJECT_VERSION)" | grep -q ".dev") || (gh release view $(PYPROJECT_VERSION) >/dev/null 2>&1); \
	then echo ""; else echo "$(PYPROJECT_VERSION)"; fi)

# paths
SRC_DIR?=$(PYPROJECT_NAME)
TESTS_DIR?=tests

.PHONY: help
help: ## This help message
	@grep -E '^[a-zA-Z0-9/_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sed 's/.*Makefile[^:]*://g' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

$(POETRY_LOCK):
$(POETRY_VENV_STAMP): pyproject.toml poetry.toml $(POETRY_LOCK)
	@if [ -z $(POETRY) ]; then echo Poetry could not be found. See https://python-poetry.org/docs/; exit 2; fi
	@$(POETRY) $(POETRY_SETUP_COMMAND) $(POETRY_OUTPUT_ARGS) && \
		touch $(POETRY_VENV_STAMP)

.PHONY: venv/create
venv/create: $(POETRY_VENV_STAMP) ## setup the python virtual environment

.PHONY: venv/lock
venv/lock: ## udpates the poetry lock file
	@$(POETRY) lock

.PHONY: venv/update
venv/update: venv/create ## udpates the python dependencies
	@$(POETRY) update

.PHONY: venv/add
venv/add: venv/create ## add a python dependency (must specify the DEP var)
	@$(POETRY) add $(DEP)

.PHONY: venv/add/dev
venv/add/dev: venv/create ## add a python dev dependency (must specify the DEP var)
	@$(POETRY) add -G dev $(DEP)

.PHONY: venv/outdated
venv/outdated: venv/create ## list outdated dependencies
	@$(POETRY) show -oT

.PHONY: venv/clean
venv/clean: ## clean the python virtual environment
	@rm -rf $(POETRY_VENV)

.PHONY: cache/clean
cache/clean: ## clean local caches (mypy, pytest, etc.)
	@rm -rf .api-doc .mypy_cache .pytest_cache .ruff_cache && \
		find . -type d -name __pycache__ -print0 | xargs -0 rm -rf

.PHONY: clean
clean: venv/clean cache/clean ## clean the dev environment (venv & caches)

.PHONY: setup
setup: venv/create ## setups the dev environment

.PHONY: lint/style
lint/style: venv/create ## run formatting linters
	@$(POETRY_RUN) black --check $(SRC_DIR) $(TESTS_DIR) && \
		$(POETRY_RUN) ruff check $(SRC_DIR) $(TESTS_DIR)

.PHONY: lint/type
lint/type: venv/create ## run the static type checking
	@$(POETRY_RUN) mypy --strict $(SRC_DIR) $(TESTS_DIR)

.PHONY: lint
lint: lint/style lint/type ## run linting

.PHONY: lint/fix
lint/fix: venv/create ## run linting and fix issues
	@$(POETRY_RUN) black $(SRC_DIR) $(TESTS_DIR) && \
		$(POETRY_RUN) ruff check --fix --extend-select I001 $(SRC_DIR) $(TESTS_DIR)

.PHONY: test
test: ONLY?=*
test: venv/create ## run unit tests
	@$(POETRY_RUN) pytest -q $(TESTS_DIR)/test_*$(ONLY)*.py

.PHONY: test/verbose
test/verbose: ONLY?=*
test/verbose: ## run unit tests with more verbosity
	@$(POETRY_RUN) pytest -s $(TESTS_DIR)/test_*$(ONLY)*.py

.PHONY: test/watch
test/watch: ONLY?=*
test/watch: ## run unit tests on every code change
	@$(POETRY_RUN) ptw --clear --now --patterns '$(SRC_DIR)/*.py,$(SRC_DIR)/**/*.py,$(TESTS_DIR)/*.py' . \
		$(TESTS_DIR)/test_*$(ONLY)*.py --ignore=$(SRC_DIR) -q

.PHONY: build
build: venv/create ## build the project (wheel & source archive)
	@$(POETRY) build

.PHONY: version
version: ## output the current version of the project
	@echo $(PYPROJECT_VERSION)

.PHONY: release/version
release/version: ## output the version to release, if any
	@echo $(RELEASE_VERSION)

.PHONY: release/gh
release/gh: ## create a github release
	@if [ -n "$(RELEASE_VERSION)" ]; then \
		gh release create "$(RELEASE_VERSION)" --generate-notes; \
	else \
		echo "Version $(PYPROJECT_VERSION) has already been released or is a dev version"; \
	fi
