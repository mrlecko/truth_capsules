// Witness languages + capsules missing witnesses

// Languages
MATCH (c:Capsule)-[:HAS_WITNESS]->(w:Witness)
RETURN coalesce(w.language,'(unknown)') AS language, count(*) AS n
ORDER BY n DESC;

// Missing witness list
MATCH (c:Capsule)
WHERE NOT (c)-[:HAS_WITNESS]->(:Witness)
RETURN c.identifier AS id
ORDER BY id;
