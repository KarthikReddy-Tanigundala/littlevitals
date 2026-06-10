#!/usr/bin/env bash
# Thin wrapper around the canonical cross-platform Python orchestrator.
# Usage: ./run_all_ingestion.sh --source snapshot --dry-run
set -euo pipefail
python "$(dirname "$0")/run_all_ingestion.py" "$@"
