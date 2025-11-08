// Coverage + domain breakdown

// 1) Domain breakdown
MATCH (c:Capsule)
RETURN c.domain AS domain, count(*) AS n
ORDER BY n DESC;

// 2) Witness coverage
MATCH (c:Capsule)
OPTIONAL MATCH (c)-[r:HAS_WITNESS]->(:Witness)
WITH count(DISTINCT c) AS total,
     count(DISTINCT CASE WHEN r IS NOT NULL THEN c END) AS with_witness
RETURN total, with_witness, round(100.0*with_witness/total,1) AS pct;
