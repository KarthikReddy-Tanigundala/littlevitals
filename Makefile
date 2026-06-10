# LittleVitals task runner (POSIX make). Windows users: see make.ps1.
DBT_FLAGS := --project-dir littlevitals_dbt --profiles-dir littlevitals_dbt

.PHONY: help setup fixtures deps build test docs serve lint ci clean

help:           ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-12s %s\n", $$1, $$2}'

setup:          ## Create venv + install dependencies
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

fixtures:       ## (Re)generate deterministic synthetic fixtures
	python data/sample/generate_sample_data.py

deps:           ## Install dbt packages
	dbt deps $(DBT_FLAGS)

build: deps fixtures ## Run + test the whole pipeline on DuckDB
	dbt build $(DBT_FLAGS)

test:           ## Run tests only
	dbt test $(DBT_FLAGS)

docs:           ## Generate dbt docs (catalog + manifest)
	dbt docs generate $(DBT_FLAGS)

serve: docs     ## Serve the dbt docs lineage site locally
	dbt docs serve $(DBT_FLAGS)

lint:           ## Lint SQL with sqlfluff
	sqlfluff lint littlevitals_dbt/models

ci:             ## Full CI gate (DuckDB target, no secrets)
	dbt deps $(DBT_FLAGS) && dbt build $(DBT_FLAGS) --target ci

clean:          ## Remove build artefacts
	dbt clean $(DBT_FLAGS)
