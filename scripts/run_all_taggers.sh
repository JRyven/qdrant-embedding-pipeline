#!/usr/bin/env bash
set -euo pipefail

echo "Running all taggers: propagation, k-NN, cluster, LLM"
PY=python3

bash scripts/run_smoke_local.sh

echo "-> propagation"
$PY scripts/tag_propagation.py

echo "-> k-NN"
$PY scripts/tag_knn.py

echo "-> cluster"
$PY scripts/tag_cluster.py

echo "-> LLM-like"
$PY scripts/tag_llm.py

echo "All taggers completed. Results in mock-results-* directories."
