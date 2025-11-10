# Knowledge Graph Readiness Guide

Truth Capsules can be exported to RDF (for semantic web/SPARQL) and property graphs (for Neo4j/Memgraph). This makes your capsules queryable, analyzable, and integrable with knowledge graph ecosystems.

---

## Quick Start (5 minutes)

### 1) Install Dependencies

```bash
pip install rdflib pyshacl pyyaml
```

### 2) Export Knowledge Graph

From the `truth-capsules-v1` directory:

```bash
python scripts/export_kg.py
```

**Outputs:**
- `artifacts/out/capsules.ttl` - RDF/Turtle format for SPARQL queries
- `artifacts/out/capsules.ndjson` - NDJSON-LD for property graph import

**Example output:**
```
[KG] ✅ Export complete!
     Capsules: 24
     Bundles: 6
     RDF triples: 451
```

### 3) Validate with SHACL

SHACL validates that your RDF conforms to the Truth Capsules ontology:

```bash
pyshacl -s shacl/truthcapsule.shacl.ttl \
        -m \
        -f human \
        artifacts/out/capsules.ttl
```

**Expected output:**
```
Conforms: True
```

If validation fails, you'll see specific errors pointing to the problematic capsule or witness.

---

## Query with SPARQL

Load `artifacts/out/capsules.ttl` into any triple store (or use `rdflib` in Python) and run the included queries:

### List All Capsules

```bash
# Using rdflib (example)
python -c "
from rdflib import Graph
g = Graph()
g.parse('artifacts/out/capsules.ttl')
for row in g.query(open('queries/list_capsules.sparql').read()):
    print(row)
"
```

**Included Queries:**

1. **`queries/list_capsules.sparql`**
   Lists all capsules with their IDs and titles

2. **`queries/capsules_by_domain.sparql`**
   Counts capsules grouped by domain (llm, business, ops, etc.)

3. **`queries/capsules_with_python_witness.sparql`**
   Finds capsules that have executable Python witnesses

---

## Load into Neo4j

### Prerequisites

1. **Neo4j Desktop or Server** installed (4.x or 5.x)
2. **APOC plugin** enabled
3. **File import** configured:
   - Place `capsules.ndjson` in Neo4j's `import` directory, or
   - Configure `dbms.directories.import` in `neo4j.conf`

### Quick Load

1. **Copy the NDJSON file:**

   ```bash
   # Example: Neo4j Desktop import folder
   cp artifacts/out/capsules.ndjson ~/Library/Application\ Support/Neo4j/Desktop/Application/neo4jDatabases/database-*/installation-*/import/
   ```

2. **Run the Cypher script:**

   In Neo4j Browser:

   ```cypher
   :source scripts/load_neo4j.cypher
   ```

   Or using `cypher-shell`:

   ```bash
   cat scripts/load_neo4j.cypher | cypher-shell -u neo4j -p password
   ```

### Verify Import

Run this query in Neo4j Browser:

```cypher
MATCH (c:Capsule)-[r:HAS_WITNESS]->(w:Witness)
RETURN c.identifier, c.title, w.language
LIMIT 10
```

You should see Capsule nodes connected to Witness nodes.

---

## Understanding the Data Model

### RDF Model (Turtle)

**Namespaces:**
- `tc:` = `https://w3id.org/tc#` (Truth Capsules vocabulary)
- `dct:` = `http://purl.org/dc/terms/` (Dublin Core)

**Key Classes:**
- `tc:Capsule` - A truth capsule
- `tc:Witness` - An executable witness/validation
- `tc:Bundle` - A collection of capsules

**Key Properties:**
- `tc:hasWitness` - Links capsule to witnesses
- `tc:inBundle` - Links capsule to bundles
- `tc:statement` - The core truth statement
- `tc:domain` - Capsule domain (llm, business, etc.)
- `tc:codeHash` - SHA-256 of witness code (security)

### Property Graph Model (Neo4j)

**Nodes:**
- `(:Capsule)` with properties: `iri`, `identifier`, `title`, `statement`, `domain`, `version`
- `(:Witness)` with properties: `iri`, `language`, `codeHash`, `codeRef`

**Relationships:**
- `(Capsule)-[:HAS_WITNESS]->(Witness)`

---

## Security & Provenance

### Code Hashing

Witnesses with inline `code` are **hashed** (SHA-256) but the code itself is **not exported** to the knowledge graph. This prevents accidental exposure of sensitive logic.

**What is exported:**
- `codeHash`: SHA-256 of normalized code (LF endings, trimmed lines)
- `codeRef`: URI reference if using external code

**What is NOT exported:**
- The actual witness code

### Hash Stability

Code is normalized before hashing:
- Line endings converted to LF (`\n`)
- Trailing spaces removed per line
- YAML `|-` block scalar style already removes final newline

This ensures the same code produces the same hash across platforms.

---

## Advanced Usage

### Custom SPARQL Queries

Write your own queries! Example:

```sparql
PREFIX tc: <https://w3id.org/tc#>
PREFIX dct: <http://purl.org/dc/terms/>

# Find high-sensitivity capsules
SELECT ?id ?title WHERE {
  ?c a tc:Capsule ;
     dct:identifier ?id ;
     dct:title ?title ;
     tc:sensitivity "high" .
}
```

### Integration with External Tools

**Apache Jena Fuseki:**
```bash
# Load into Fuseki triple store
s-put http://localhost:3030/ds/data default artifacts/out/capsules.ttl
```

**GraphDB:**
```bash
# Import via GraphDB Workbench GUI or REST API
```

**Memgraph:**
```bash
# Similar to Neo4j, uses openCypher
```

---

## CI/CD Integration

See `.github/workflows/kg-smoke.yml` for an example GitHub Actions workflow that:

1. Exports the knowledge graph
2. Validates with SHACL
3. Fails CI if validation errors occur

This ensures your capsule library stays valid as it evolves.

---

## Troubleshooting

### SHACL Validation Fails

**Error:** `sh:minCount 1` violation on `dct:identifier`

**Fix:** Ensure all capsules have an `id` field in their YAML.

---

**Error:** `sh:in ("python" "node" "bash")` violation

**Fix:** Witness `language` must be one of: `python`, `node`, `bash`.

---

**Error:** `sh:xone` violation on codeHash/codeRef

**Fix:** Witnesses must have **either** inline `code` (→ `codeHash`) **or** `code_ref` (→ `codeRef`), not both or neither.

---

### Neo4j Import Fails

**Error:** `Couldn't load the external resource at: file:///artifacts/...`

**Fix:**
1. Check `dbms.directories.import` setting in `neo4j.conf`
2. Ensure `capsules.ndjson` is in the configured import directory
3. Use absolute path or adjust the path in `load_neo4j.cypher`

---

**Error:** `Unknown function 'apoc.load.json'`

**Fix:** Install the APOC plugin via Neo4j Desktop or manually download from [neo4j-contrib/neo4j-apoc-procedures](https://github.com/neo4j-contrib/neo4j-apoc-procedures).

---

## Next Steps

- **Add more SPARQL queries** for your specific use cases
- **Integrate with semantic web tools** (Protégé, TopBraid Composer)
- **Build dashboards** using Neo4j Bloom or Memgraph Lab
- **Contribute back** improved ontology or queries

---

## Technical Notes

### Why RDF + Property Graphs?

**RDF (Turtle):**
- Standard semantic web format
- Rich ontology support (OWL, RDFS, SHACL)
- Federated queries across knowledge graphs (SPARQL FEDERATION)
- Used by Wikidata, DBpedia, government data portals

**Property Graphs (NDJSON-LD):**
- Optimized for graph databases (Neo4j, Memgraph, TigerGraph)
- High-performance traversals
- Developer-friendly Cypher queries
- Great for recommendation systems, fraud detection, network analysis

Truth Capsules supports **both** to maximize interoperability.

### Ontology Design Philosophy

- **Minimal but extensible** - Core properties only, easy to extend
- **Standards-based** - Uses Dublin Core terms where possible
- **Provenance-first** - Author, org, license, review status built-in
- **Security-aware** - Code hashes instead of code export

---

## References

- [RDF 1.1 Turtle Specification](https://www.w3.org/TR/turtle/)
- [SHACL Specification](https://www.w3.org/TR/shacl/)
- [SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/)
- [Neo4j APOC Documentation](https://neo4j.com/labs/apoc/)
- [rdflib Documentation](https://rdflib.readthedocs.io/)
- [pyshacl Documentation](https://github.com/RDFLib/pySHACL)

---

**Questions?** Open an issue or contribute improvements to the ontology!
