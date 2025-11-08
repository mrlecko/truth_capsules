// Truth Capsules - Neo4j Property Graph Loader
//
// Loads capsules from NDJSON-LD into Neo4j using APOC
// Works with Neo4j 4.x+, Memgraph has similar syntax
//
// Prerequisites:
//   1. APOC plugin installed
//   2. File import path configured: dbms.directories.import
//   3. capsules.ndjson accessible at file:///artifacts/out/capsules.ndjson
//
// Usage in Neo4j Browser:
//   :RUN scripts/load_neo4j.cypher

// Create constraints for uniqueness
CREATE CONSTRAINT capsule_pk IF NOT EXISTS FOR (c:Capsule) REQUIRE c.iri IS UNIQUE;
CREATE CONSTRAINT witness_pk IF NOT EXISTS FOR (w:Witness) REQUIRE w.iri IS UNIQUE;

// Load capsules from NDJSON
CALL apoc.load.json("file:///artifacts/out/capsules.ndjson") YIELD value AS v
MERGE (c:Capsule {iri: v['@id']})
  SET c.identifier = v.identifier,
      c.title      = v.title,
      c.statement  = v.statement,
      c.domain     = v.domain,
      c.version    = v.version
WITH c, v
UNWIND coalesce(v.assumption, []) AS a
  SET c.assumptions = coalesce(c.assumptions, []) + a
WITH c, v
UNWIND coalesce(v.hasWitness, []) AS w
MERGE (wNode:Witness {iri: w['@id']})
  SET wNode.language = w.language,
      wNode.codeHash = w.codeHash,
      wNode.codeRef  = w.codeRef
MERGE (c)-[:HAS_WITNESS]->(wNode);
