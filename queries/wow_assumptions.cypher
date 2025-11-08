// Assumption vocab + co-occurrence pairs (requires APOC text helpers)

// Vocab
WITH ['the','and','to','of','a','in','for','is','are','be','with','or','that','on','as','at','by','it','an'] AS stop
MATCH (c:Capsule) UNWIND coalesce(c.assumptions,[]) AS a
WITH apoc.text.clean(toLower(a)) AS t, stop
WITH [x IN apoc.text.split(t,'[^a-z0-9]+')
      WHERE size(x)>2 AND NOT x IN stop] AS toks
UNWIND toks AS tok
RETURN tok, count(*) AS freq
ORDER BY freq DESC
LIMIT 25;

// Co-occurrence pairs
MATCH (c:Capsule)
UNWIND coalesce(c.assumptions,[]) AS a
WITH c, collect(distinct trim(a)) AS L
UNWIND L AS a1
UNWIND L AS a2
WITH a1,a2 WHERE a1 < a2
RETURN a1 AS assumption1, a2 AS assumption2, count(*) AS together
ORDER BY together DESC
LIMIT 25;
