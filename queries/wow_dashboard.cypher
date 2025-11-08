// One-shot dashboard feel: run all at once in Browser

// Coverage
MATCH (c:Capsule)
OPTIONAL MATCH (c)-[r:HAS_WITNESS]->(:Witness)
WITH count(DISTINCT c) AS total,
     count(DISTINCT CASE WHEN r IS NOT NULL THEN c END) AS with_witness
RETURN 'Coverage' AS metric, total AS total_capsules, with_witness, round(100.0*with_witness/total,1) AS pct;

// Top Socratic
MATCH (c:Capsule) UNWIND coalesce(c.socratic,[]) AS q
RETURN 'Top Socratic' AS section, q, count(*) AS uses
ORDER BY uses DESC, q LIMIT 10;

// Witness languages
MATCH (c:Capsule)-[:HAS_WITNESS]->(w:Witness)
RETURN 'WitnessLang' AS section, coalesce(w.language,'(unknown)') AS lang, count(*) AS n
ORDER BY n DESC;

// Assumption co-occurrence sample
MATCH (c:Capsule)
UNWIND coalesce(c.assumptions,[]) AS a
WITH c, collect(distinct trim(a)) AS L
UNWIND L AS a1
UNWIND L AS a2
WITH a1,a2 WHERE a1 < a2
RETURN 'AssumpPairs' AS section, a1, a2, count(*) AS together
ORDER BY together DESC LIMIT 10;
