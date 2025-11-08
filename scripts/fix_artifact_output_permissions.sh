# from repo root
ls -ld artifacts/out
# If not owned by you, fix it:
sudo chown -R "$(id -u)":"$(id -g)" artifacts/out
chmod -R u+rwX,go+rX artifacts/out

# sanity: can you write a file?
touch artifacts/out/_perm_test && rm artifacts/out/_perm_test

####

python scripts/export_kg.py
# Expect:
#   artifacts/out/capsules.ttl
#   artifacts/out/capsules.ndjson

####

# https://github.com/neo4j/apoc/releases/download/5.26.16/apoc-5.26.16-core.jar
do

NEO_VER=5.26.16
APOC_VER=2025.10

mkdir -p .neo4j/plugins .neo4j/data .neo4j/logs
curl -fL -o .neo4j/plugins/apoc-${APOC_VER}-extended.jar \
  https://github.com/neo4j/apoc/releases/download/${APOC_VER}/apoc-${APOC_VER}-extended.jar

docker rm -f neo4j-capsules 2>/dev/null || true
docker run -d --name neo4j-capsules \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_apoc_import_file_enabled=true \
  -e NEO4J_apoc_export_file_enabled=true \
  -e NEO4J_apoc_import_file_use__neo4j__config=true \
  -e NEO4J_dbms_security_procedures_unrestricted='apoc.*' \
  -e NEO4J_dbms_security_procedures_allowlist='apoc.*' \
  -v "$PWD/.neo4j/data":/data \
  -v "$PWD/.neo4j/logs":/logs \
  -v "$PWD/.neo4j/plugins":/plugins:ro \
  -v "$PWD/.neo4j/plugins":/var/lib/neo4j/plugins:ro \
  -v "$PWD/artifacts/out":/var/lib/neo4j/import/artifacts/out:ro \
  -v "$PWD/scripts":/opt/scripts:ro \
  "neo4j:${NEO_VER}"

until docker exec neo4j-capsules cypher-shell -u neo4j -p password "RETURN 1;" >/dev/null 2>&1; do sleep 1; done
docker exec neo4j-capsules cypher-shell -u neo4j -p password "CALL apoc.version();"
docker exec neo4j-capsules cypher-shell -u neo4j -p password \
  "SHOW PROCEDURES YIELD name WHERE name STARTS WITH 'apoc.load' RETURN name;"

docker exec -i neo4j-capsules cypher-shell -u neo4j -p password -f /opt/scripts/load_neo4j.cypher
docker exec neo4j-capsules cypher-shell -u neo4j -p password 'MATCH (c:Capsule) RETURN count(c) AS capsules;'
docker exec neo4j-capsules cypher-shell -u neo4j -p password 'MATCH (:Capsule)-[r:HAS_WITNESS]->(:Witness) RETURN count(r) AS witness_edges;'
