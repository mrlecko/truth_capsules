#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "using ROOT as: $ROOT"
RUN="$ROOT/scripts/neo4j_query.sh"

run() {
  local path="$1"
  printf "\n\n===== %s =====\n" "$(basename "$path")"
  "$RUN" "$path"
}

run "$ROOT/queries/wow_coverage.cypher"
run "$ROOT/queries/wow_pedagogy.cypher"
run "$ROOT/queries/wow_witnesses.cypher"
run "$ROOT/queries/wow_assumptions.cypher"
run "$ROOT/queries/wow_release_notes.cypher"
run "$ROOT/queries/wow_previews.cypher"

echo -e "\nTip: build/cleanup the Assumption network:"
echo "  $RUN $ROOT/queries/build_assumption_network.cypher"
echo "  $RUN $ROOT/queries/cleanup_assumption_network.cypher"

echo -e "\nSearch template with param:"
echo "  $RUN $ROOT/queries/wow_search_template.cypher -- --param q='risk'"
