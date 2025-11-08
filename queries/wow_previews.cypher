// Preview first 120 chars of statements
MATCH (c:Capsule)
RETURN c.identifier AS id, left(coalesce(c.statement,''),120) AS preview
ORDER BY id;
