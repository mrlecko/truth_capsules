// Parameterized text search across title, assumptions, pedagogy
// Usage with cypher-shell: --param q='risk'

WITH toLower($q) AS q
MATCH (c:Capsule)
WHERE toLower(coalesce(c.title,'')) CONTAINS q
   OR any(x IN coalesce(c.assumptions,[]) WHERE toLower(x) CONTAINS q)
   OR any(x IN coalesce(c.socratic,[])   WHERE toLower(x) CONTAINS q)
   OR any(x IN coalesce(c.aphorisms,[])  WHERE toLower(x) CONTAINS q)
RETURN c.identifier AS id, coalesce(c.title,'') AS title
LIMIT 20;
