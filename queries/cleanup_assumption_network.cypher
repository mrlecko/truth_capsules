// Cleanup assumption graph (idempotent-ish)
MATCH ()-[r:CO_OCCURS_WITH]->() DELETE r;
MATCH ()-[r:HAS_ASSUMPTION]->() DELETE r;
MATCH (a:Assumption) DELETE a;
