#!/usr/bin/env bash
set -Eeuo pipefail

# --- Get / Store the apoc jar for 4.4 -----------------------------------------
#mkdir -p .neo4j44/plugins
#curl -fL -o .neo4j44/plugins/apoc-4.4.0.39-all.jar \
#  https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/download/4.4.0.39/apoc-4.4.0.39-all.jar


# --- Config (override via env if needed) --------------------------------------
CONTAINER_NAME="${CONTAINER_NAME:-neo4j44}"
IMAGE="${IMAGE:-neo4j:4.4}"
NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_PASS="${NEO4J_PASS:-password}"

# Host export dir (already produced by scripts/export_kg.py)
HOST_OUT_DIR="${HOST_OUT_DIR:-$PWD/artifacts/out}"

# Inside-container import root and file URL
IMPORT_ROOT="/import"
MOUNTED_OUT_DIR="$IMPORT_ROOT/artifacts/out"
FILE_URL="file:///artifacts/out/capsules.ndjson"

# --- Helpers ------------------------------------------------------------------
say() { printf '\n==> %s\n' "$*"; }
die() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }

bolt_ping() {
  docker exec "$CONTAINER_NAME" cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASS" --encryption=false \
    "RETURN 1 AS ok" >/dev/null
}

# ---- Robust Bolt wait: do NOT die on early connection refused ---------------
bolt_wait() {
  say "Waiting for Bolt to be ready…"
  local tries=0
  while true; do
    # Ignore failures until it works
    if docker exec "$CONTAINER_NAME" cypher-shell \
        -u "$NEO4J_USER" -p "$NEO4J_PASS" --encryption=false \
        "RETURN 1 AS ok" >/dev/null 2>&1; then
      say "Bolt is ready."
      return 0
    fi
    tries=$((tries+1))
    if [ "$tries" -ge 120 ]; then
      die "Neo4j did not become ready in 120s."
    fi
    sleep 1
  done
}

# ---- Cypher helper that won't kill the script on error -----------------------
cypher_try() {
  docker exec "$CONTAINER_NAME" cypher-shell \
    -u "$NEO4J_USER" -p "$NEO4J_PASS" --encryption=false "$@" \
    >/dev/null 2>&1
}

# ---- APOC check: apoc.version() is a FUNCTION, not CALL-able -----------------
say "Checking APOC availability…"
if ! cypher_try "RETURN apoc.version() AS apoc_version"; then
  die "APOC not available. On Neo4j 4.4 use NEO4JLABS_PLUGINS='[\"apoc\"]' (not NEO4J_PLUGINS)."
fi


cypher() {
  docker exec "$CONTAINER_NAME" cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASS" --encryption=false "$@"
}

# --- Pre-flight ---------------------------------------------------------------
[ -d "$HOST_OUT_DIR" ] || die "Missing $HOST_OUT_DIR. Run your KG export first."
[ -f "$HOST_OUT_DIR/capsules.ndjson" ] || die "Missing $HOST_OUT_DIR/capsules.ndjson. Run: python scripts/export_kg.py"

# --- Start fresh container ----------------------------------------------------
say "Stopping/removing any old container: $CONTAINER_NAME"
docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true

say "Starting $IMAGE with APOC enabled and import dir mounted"
docker run -d --name "$CONTAINER_NAME" \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH="${NEO4J_USER}/${NEO4J_PASS}" \
  -e NEO4JLABS_PLUGINS='["apoc"]' \
  -e NEO4J_dbms_security_procedures_allowlist='apoc.*' \
  -e NEO4J_apoc_import_file_enabled=true \
  -e NEO4J_apoc_export_file_enabled=true \
  -e NEO4J_dbms_directories_import="$IMPORT_ROOT" \
  -v "$HOST_OUT_DIR":"$MOUNTED_OUT_DIR":ro \
  "$IMAGE" >/dev/null

bolt_wait

# --- Check APOC ---------------------------------------------------------------
say "Checking APOC availability…"
if ! cypher "RETURN apoc.version() AS apoc_version;"; then
  die "APOC not available. Ensure image=$IMAGE and NEO4JLABS_PLUGINS are correct."
fi

# --- Show import visibility ---------------------------------------------------
say "Listing mounted import dir inside container:"
docker exec "$CONTAINER_NAME" bash -lc "ls -l $MOUNTED_OUT_DIR || true"

# --- Constraints (one statement per call) ------------------------------------
say "Creating constraints (idempotent)…"
cypher "CREATE CONSTRAINT capsule_pk IF NOT EXISTS FOR (c:Capsule) REQUIRE c.iri IS UNIQUE" || true
cypher "CREATE CONSTRAINT witness_pk IF NOT EXISTS FOR (w:Witness) REQUIRE w.iri IS UNIQUE" || true

# --- Load Capsules (sandbox-safe: no apoc.meta.*) -----------------------------
say "Loading capsules from $FILE_URL …"
cypher "
WITH 'file:///artifacts/out/capsules.ndjson' AS URL
CALL apoc.load.json(URL) YIELD value AS v0

// Basic fields (string-safe)
WITH v0,
     toString(coalesce(v0['@id'],'')) AS iri,
     toString(coalesce(v0.identifier, v0['@id'])) AS identifier,
     toString(coalesce(v0.title,'')) AS title,
     toString(coalesce(v0.statement,'')) AS statement,
     toString(coalesce(v0.domain,'')) AS domain,
     toString(coalesce(v0.version,'')) AS version

// ---- assumptions: allow string | list | map{"@value"} ----
CALL {
  WITH v0
  WITH coalesce(v0.assumption, v0.assumptions, []) AS A
  // make sure we always UNWIND a list
  UNWIND (CASE WHEN apoc.meta.type(A) = 'LIST' THEN A ELSE [A] END) AS a
  WITH CASE WHEN apoc.meta.type(a) = 'MAP' THEN a['@value'] ELSE a END AS ax
  RETURN [x IN collect(toString(ax)) WHERE x <> ''] AS assumptions_list
}

// ---- pedagogy: allow string | list | {kind,text} maps ----
CALL {
  WITH v0
  WITH coalesce(v0.pedagogy, []) AS P
  UNWIND (CASE WHEN apoc.meta.type(P) = 'LIST' THEN P ELSE [P] END) AS p
  WITH
    CASE WHEN apoc.meta.type(p)='MAP' THEN toString(p.kind) ELSE '' END AS kind,
    CASE WHEN apoc.meta.type(p)='MAP' THEN toString(coalesce(p.text,p['@value'])) ELSE toString(p) END AS text
  RETURN
    [x IN collect(CASE WHEN kind='Socratic' AND text<>'' THEN text END) WHERE x IS NOT NULL] AS socratic_list,
    [x IN collect(CASE WHEN kind='Aphorism' AND text<>'' THEN text END) WHERE x IS NOT NULL] AS aphorisms_list
}

// ---- witnesses: allow singleton | list; maps only ----
CALL {
  WITH v0
  WITH coalesce(v0.hasWitness, []) AS W
  UNWIND (CASE WHEN apoc.meta.type(W)='LIST' THEN W ELSE [W] END) AS w
  WITH CASE WHEN apoc.meta.type(w)='MAP' THEN w ELSE NULL END AS wmap
  RETURN [x IN collect(wmap) WHERE x IS NOT NULL] AS witnesses
}

// Upsert capsule node
MERGE (c:Capsule {iri: iri})
  SET c.identifier  = identifier,
      c.title       = title,
      c.statement   = statement,
      c.domain      = domain,
      c.version     = version,
      c.assumptions = assumptions_list,
      c.socratic    = socratic_list,
      c.aphorisms   = aphorisms_list

// Link witnesses
WITH c, witnesses
UNWIND witnesses AS w
MERGE (wNode:Witness {iri: toString(w['@id'])})
  SET wNode.language = toString(coalesce(w.language,'')),
      wNode.codeHash = toString(coalesce(w.codeHash,'')),
      wNode.codeRef  = toString(coalesce(w.codeRef,''))
MERGE (c)-[:HAS_WITNESS]->(wNode);
"

# --- Load Bundles and Profiles ------------------------------------------------
say "Loading bundles and profiles from $FILE_URL …"
cypher "
WITH 'file:///artifacts/out/capsules.ndjson' AS URL
CALL apoc.load.json(URL) YIELD value AS v0
WITH v0,
     CASE
       WHEN v0['@type'] = 'Bundle' THEN 'Bundle'
       WHEN v0['@type'] = 'Profile' THEN 'Profile'
       ELSE 'Other'
     END AS nodeType

// Handle Bundles
FOREACH (x IN CASE WHEN nodeType = 'Bundle' THEN [1] ELSE [] END |
  MERGE (b:Bundle {iri: toString(v0['@id'])})
    SET b.identifier = toString(coalesce(v0.identifier, '')),
        b.name       = toString(coalesce(v0.name, v0.identifier, ''))
)

// Handle Profiles
FOREACH (x IN CASE WHEN nodeType = 'Profile' THEN [1] ELSE [] END |
  MERGE (p:Profile {iri: toString(v0['@id'])})
    SET p.identifier     = toString(coalesce(v0.identifier, '')),
        p.title          = toString(coalesce(v0.title, '')),
        p.description    = toString(coalesce(v0.description, '')),
        p.version        = toString(coalesce(v0.version, '')),
        p.kind           = toString(coalesce(v0.kind, '')),
        p.responseFormat = toString(coalesce(v0.responseFormat, ''))
);
"

# --- Create Profile->Capsule relationships -----------------------------------
say "Creating Profile->Capsule relationships…"
cypher "
WITH 'file:///artifacts/out/capsules.ndjson' AS URL
CALL apoc.load.json(URL) YIELD value AS v0
WHERE v0['@type'] = 'Profile'
MATCH (p:Profile {iri: toString(v0['@id'])})
WITH p, coalesce(v0.includesCapsule, []) AS capsuleRefs
UNWIND capsuleRefs AS cref
WITH p, toString(cref) AS capsulePattern
// Try to match capsules by ID pattern (e.g., 'pedagogy.socratic' matches capsules with that prefix)
MATCH (c:Capsule)
WHERE c.identifier CONTAINS capsulePattern OR c.identifier = capsulePattern
MERGE (p)-[:INCLUDES_CAPSULE]->(c);
"

# --- Sanity queries -----------------------------------------------------------
say "Sanity: counts"
cypher "MATCH (c:Capsule) RETURN count(c) AS capsules"
cypher "MATCH (b:Bundle) RETURN count(b) AS bundles"
cypher "MATCH (p:Profile) RETURN count(p) AS profiles"
cypher "MATCH (:Capsule)-[r:HAS_WITNESS]->(:Witness) RETURN count(r) AS witness_edges"
cypher "MATCH (:Profile)-[r:INCLUDES_CAPSULE]->(:Capsule) RETURN count(r) AS profile_capsule_edges"

say "Sample nodes"
cypher "MATCH (c:Capsule) RETURN c.iri AS iri, c.title AS title ORDER BY c.iri LIMIT 3"
cypher "MATCH (p:Profile) RETURN p.iri AS iri, p.title AS title ORDER BY p.iri LIMIT 3"

say "Done. Open http://localhost:7474 (user=$NEO4J_USER / pass=$NEO4J_PASS)."
