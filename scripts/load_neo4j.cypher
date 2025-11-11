// Truth Capsules - Neo4j Property Graph Loader
//
// Loads capsules, bundles, profiles, and witnesses from NDJSON-LD into Neo4j using APOC
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
CREATE CONSTRAINT bundle_pk IF NOT EXISTS FOR (b:Bundle) REQUIRE b.iri IS UNIQUE;
CREATE CONSTRAINT profile_pk IF NOT EXISTS FOR (p:Profile) REQUIRE p.iri IS UNIQUE;

// Load all records from NDJSON (Capsules, Bundles, Profiles)
CALL apoc.load.json("file:///artifacts/out/capsules.ndjson") YIELD value AS v

// Process based on @type
WITH v,
     CASE
       WHEN v['@type'] = 'Capsule' THEN 'Capsule'
       WHEN v['@type'] = 'Bundle' THEN 'Bundle'
       WHEN v['@type'] = 'Profile' THEN 'Profile'
       ELSE 'Unknown'
     END AS nodeType

// Handle Capsules
FOREACH (x IN CASE WHEN nodeType = 'Capsule' THEN [1] ELSE [] END |
  MERGE (c:Capsule {iri: v['@id']})
    SET c.identifier = v.identifier,
        c.title      = v.title,
        c.statement  = v.statement,
        c.domain     = v.domain,
        c.version    = v.version,
        c.assumptions = coalesce(v.assumption, [])
)

// Handle Bundles
FOREACH (x IN CASE WHEN nodeType = 'Bundle' THEN [1] ELSE [] END |
  MERGE (b:Bundle {iri: v['@id']})
    SET b.identifier = v.identifier,
        b.name       = v.name
)

// Handle Profiles
FOREACH (x IN CASE WHEN nodeType = 'Profile' THEN [1] ELSE [] END |
  MERGE (p:Profile {iri: v['@id']})
    SET p.identifier     = v.identifier,
        p.title          = v.title,
        p.description    = v.description,
        p.version        = v.version,
        p.kind           = v.kind,
        p.responseFormat = v.responseFormat,
        p.includesCapsule = coalesce(v.includesCapsule, [])
)

// Create relationships for Capsule witnesses
WITH v, nodeType
WHERE nodeType = 'Capsule'
MATCH (c:Capsule {iri: v['@id']})
WITH c, coalesce(v.hasWitness, []) AS witnesses
UNWIND witnesses AS w
MERGE (wNode:Witness {iri: w['@id']})
  SET wNode.language = w.language,
      wNode.codeHash = w.codeHash,
      wNode.codeRef  = w.codeRef
MERGE (c)-[:HAS_WITNESS]->(wNode);
