// Pedagogy heatmap + top socratic + top aphorisms

// Heatmap
MATCH (c:Capsule)
WITH c,
     size(coalesce(c.socratic,[]))  AS qs,
     size(coalesce(c.aphorisms,[])) AS aph
RETURN c.identifier AS id, qs AS socratic, aph AS aphorisms, (qs+aph) AS total
ORDER BY total DESC
LIMIT 15;

// Top socratic questions
MATCH (c:Capsule) UNWIND coalesce(c.socratic,[]) AS q
RETURN q, count(*) AS uses
ORDER BY uses DESC, q
LIMIT 20;

// Top aphorisms
MATCH (c:Capsule) UNWIND coalesce(c.aphorisms,[]) AS a
RETURN a, count(*) AS uses
ORDER BY uses DESC, a
LIMIT 20;
