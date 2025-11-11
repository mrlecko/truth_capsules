# Neo4j Queries

A curated set of fast, high‑signal Cypher queries that show off the Truth Capsules graph in Neo4j.

## Files

- **wow_coverage.cypher** - Two gauges: domain breakdown (how many capsules per domain) and witness coverage (% of capsules with at least one witness).
- **wow_pedagogy.cypher** - Pedagogy view: heatmap‑like table of Socratic/Aphorism counts per capsule plus the most frequent questions/aphorisms.
- **wow_assumptions.cypher** - Vocabulary and co‑occurrence pairs for capsule assumptions (uses APOC text helpers). Great for surfacing core concepts and phrase clusters.
- **wow_witnesses.cypher** - Witness language distribution and the list of capsules with missing witnesses.
- **wow_search_template.cypher** - Parameterized search across title, assumptions, Socratic, and aphorisms (pass `--param q='risk'`).
- **wow_release_notes.cypher** - Emits markdown bullet lines for quick release notes.
- **wow_previews.cypher** - 120‑character statement previews for a skim view.
- **build_assumption_network.cypher** - Materializes an `:Assumption` node layer and `:CO_OCCURS_WITH` edges to create a mini concept network.
- **cleanup_assumption_network.cypher** - Removes the assumption network (edges and nodes) to reset the graph.
- **wow_dashboard.cypher** - A one‑shot “dashboard” that returns multiple sections (coverage, top Socratic, witness languages, co‑occurrence sample) - great in Neo4j Browser.

## Usage

Prefer the tiny runner scripts in `scripts/`:

```bash
# Run all WOW queries (except the build/cleanup helpers):
./scripts/neo4j_wow_all.sh

# Run a single file
./scripts/neo4j_query.sh queries/wow_coverage.cypher

# Parameterized search template
./scripts/neo4j_query.sh queries/wow_search_template.cypher -- --param q='rollback'

# Build the assumption mini-network
./scripts/neo4j_query.sh queries/build_assumption_network.cypher

# Clean it up again
./scripts/neo4j_query.sh queries/cleanup_assumption_network.cypher
```

Assumptions:
- Neo4j is running and already loaded with Truth Capsules.
- If using Docker, the container name defaults to `neo4j44` (override via `NEO4J_CONTAINER`).
- Default credentials: `neo4j/password` (override via `NEO4J_USER` / `NEO4J_PASS`).

Tip: The APOC‑using query (`wow_assumptions.cypher`) requires APOC text functions (`apoc.text.*`). If you don’t have APOC, run the others first - they don’t require it.
