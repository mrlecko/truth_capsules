#!/usr/bin/env bash
set -euo pipefail

# Run a .cypher file against Neo4j (Docker or local)
# Usage: ./scripts/neo4j_query.sh queries/wow_coverage.cypher [-- --param q='risk']

FILE="${1:-}"
shift || true

if [[ -z "${FILE}" || ! -f "${FILE}" ]]; then
  echo "Usage: $0 path/to/file.cypher [-- param=value ...]" >&2
  exit 1
fi

# Config (override via env)
NEO4J_CONTAINER="${NEO4J_CONTAINER:-neo4j44}"
NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_PASS="${NEO4J_PASS:-password}"
CYPHER_SHELL="${CYPHER_SHELL:-cypher-shell}"
EXTRA_PARAMS=("$@") # e.g. -- --param q='risk'

say() { printf "\n==> %s\n" "$*"; }

# Prefer Docker if container is running
if docker ps --format '{{.Names}}' | grep -q "^${NEO4J_CONTAINER}$"; then
  say "Docker exec → ${NEO4J_CONTAINER} : ${FILE}"
  # Note: -i to pipe stdin into cypher-shell
  docker exec -i "${NEO4J_CONTAINER}" "${CYPHER_SHELL}" \
    -u "${NEO4J_USER}" -p "${NEO4J_PASS}" --encryption=false \
    "${EXTRA_PARAMS[@]}" < "${FILE}"
else
  # Fallback to local cypher-shell
  say "Local cypher-shell → ${FILE}"
  "${CYPHER_SHELL}" -u "${NEO4J_USER}" -p "${NEO4J_PASS}" --encryption=false \
    "${EXTRA_PARAMS[@]}" < "${FILE}"
fi
