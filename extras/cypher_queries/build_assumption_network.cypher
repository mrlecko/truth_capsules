// Build a small assumption node/edge network

// Nodes + links
MATCH (c:Capsule)
UNWIND coalesce(c.assumptions,[]) AS a
WITH c, trim(a) AS ax WHERE ax <> ''
MERGE (A:Assumption {text: ax})
MERGE (c)-[:HAS_ASSUMPTION]->(A);

// Co-occurrence edges with counts
MATCH (c:Capsule)-[:HAS_ASSUMPTION]->(A:Assumption)
WITH c, collect(A) AS L
UNWIND L AS a1 UNWIND L AS a2
WITH a1,a2 WHERE id(a1) < id(a2)
MERGE (a1)-[r:CO_OCCURS_WITH]->(a2)
  ON CREATE SET r.count = 1
  ON MATCH  SET r.count = r.count + 1;

// Top hubs
MATCH (A:Assumption)<-[:HAS_ASSUMPTION]-(:Capsule)
RETURN A.text, count(*) AS in_capsules
ORDER BY in_capsules DESC
LIMIT 20;
