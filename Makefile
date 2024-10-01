.ONESHELL:

SHELL := /bin/bash
VERSION := $(shell grep "^version = " ./pyproject.toml | cut -d = -f2 | tr -d '"' | tr -d " ")
SRC_DIR = flask_apispec
PY_FILES := $(shell find $(SRC_DIR) -type f -name '*.py')
NAME := $(shell basename "$$PWD")
PY_NAME := $(shell echo $(NAME) | tr "-" "_")
POETRY := poetry

PYPROJECT := pyproject.toml

export VIRTUAL_ENV_DISABLE_PROMPT = 1

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: publish
publish: build
	$(POETRY) publish -r us-central1-pypi-publish --ansi

.PHONY: lint-check
lint-check: ## Report what code does not pass linting
	$(POETRY) run black --check --config ./$(PYPROJECT) $(SRC_DIR)

.PHONY: lint-format
lint-format: ## Format code to pass the linting: this modifies source code!
	$(POETRY) run black --config ./$(PYPROJECT) $(SRC_DIR)

.PHONY: test
test:
	# $(POETRY) run coverage run --branch -m pytest --durations=10 --color=yes .
	# $(POETRY) run coverage report
	# $(POETRY) run coverage html

.PHONY: build
build: $(SWAGGER_INSTALL) dist/$(PY_NAME)-$(VERSION)-py3-none-any.whl ## Build python package

dist/$(PY_NAME)-$(VERSION)-py3-none-any.whl: $(PYPROJECT) poetry.lock $(PY_FILES) $(SWAGGER_INSTALL)
	rm -rf dist || true
	$(POETRY) build

poetry.lock: $(PYPROJECT)
	$(POETRY) lock --no-update
	touch poetry.lock #touch to update file times if nothing changed

.PHONY: clean
clean: ## Clean all Python and docker resources
	rm -rf dist || true
	rm -rf build || true
	rm -rf flask_apispec.egg-info

## NPM/Swagger stuff

SWAGGER_UI_DIST := swagger-ui-dist
SWAGGER_NODEMOD := node_modules/$(SWAGGER_UI_DIST)
SWAGGER_INSTALL := $(SRC_DIR)/static

.PHONY: install
install: $(SWAGGER_INSTALL) ## Mimicking the invoke install task in tasks.py

$(SWAGGER_INSTALL): $(SWAGGER_NODEMOD)
	rm -rf $(SWAGGER_INSTALL) || true
	cp -r $(SWAGGER_NODEMOD) $(SWAGGER_INSTALL)

$(SWAGGER_NODEMOD): package.json
	npm install
