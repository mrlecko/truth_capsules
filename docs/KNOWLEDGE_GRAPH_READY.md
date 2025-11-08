# Truth Capsules are **Knowledge-Graph Ready**

> **TL;DR**: Your YAML capsules export to standard **RDF** (Turtle) and **NDJSON-LD**, validate with **SHACL**, and load into **Neo4j/Memgraph** with one command. You get portable provenance, queryable structure, and instant graph demos-without changing how you write capsules.

---

## Why this matters (2025)

Knowledge graphs finally went mainstream. Teams expect:

* **Standards**: RDF/JSON-LD + SHACL (interoperable, vendor-neutral).
* **Provenance**: machine-verifiable links between policy, checks, and artifacts.
* **Playable demos**: Neo4j/Memgraph graphs they can click and query today.

Truth Capsules now meet those expectations out of the box.

---

## What “KG-ready” means here

1. **Export** your existing YAML → **RDF/Turtle** and **NDJSON-LD**
2. **Validate** the graph with **SHACL** shapes
3. **Query** with ready-made **SPARQL**
4. **Load** into property graphs via a tiny **Cypher** loader

No re-authoring. The exporter reads your current schema:

```yaml
id, version, domain, title, statement, assumptions[], witnesses[], provenance, applies_to[], dependencies[]
```

---

## 3-minute Quickstart

```bash
# 1) Install lightweight deps
pip install rdflib pyshacl pyyaml

# 2) Export graph artifacts (RDF + NDJSON-LD)
python scripts/export_kg.py
# → artifacts/out/capsules.ttl
# → artifacts/out/capsules.ndjson

# 3) Validate with SHACL
pyshacl -s shacl/truthcapsule.shacl.ttl -m -f human artifacts/out/capsules.ttl
# Expect: Conforms: True
```

**Neo4j demo (optional, 60s):**

```cypher
// In Neo4j Browser (APOC enabled):
:RUN scripts/load_neo4j.cypher
```

---

## Data model snapshot (minimal & standard-aligned)

* **Classes**: `tc:Capsule`, `tc:Witness`, `tc:Bundle`
* **Key properties**

  * Capsule: `dct:identifier` (from `id`), `dct:title`, `tc:statement`, `tc:domain`, `schema:version`, `tc:assumption`*
  * Witness: `tc:language`, **`tc:codeHash`** (SHA-256 of normalized inline code) or `tc:codeRef` (when code is referenced)
  * Relations: `tc:hasWitness` (Capsule → Witness), `tc:inBundle` (Capsule → Bundle)
* **IRIs**

  * Capsule: `https://w3id.org/tc/capsule/{id}`
  * Witness: `{CapsuleIRI}#w/{witness.name}`
  * Bundle:  `https://w3id.org/tc/bundle/{bundle.name}`

* Assumptions are emitted as multiple `tc:assumption` literals.

---

## Guarantees & hygiene

* **Integrity without leakage**: we emit **hashes** (`codeHash`) of inline witness code, not the code itself.
* **Stable hashing**: code is normalized (LF, trimmed trailing spaces) before hashing.
* **Shape checks**: SHACL enforces Capsule minima (id/title/statement) and basic Witness requirements (language + codeHash or codeRef).
* **No schema changes**: the exporter maps your current YAML fields as-is.

---

## Query examples

**SPARQL - List Capsules**

```sparql
PREFIX tc: <https://w3id.org/tc#>
PREFIX dct: <http://purl.org/dc/terms/>
SELECT ?id ?title WHERE {
  ?c a tc:Capsule ; dct:identifier ?id ; dct:title ?title .
} ORDER BY ?id
```

**SPARQL - Capsules by domain**

```sparql
PREFIX tc: <https://w3id.org/tc#>
SELECT ?domain (COUNT(?c) AS ?n) WHERE {
  ?c a tc:Capsule ; tc:domain ?domain .
} GROUP BY ?domain ORDER BY DESC(?n)
```

**Neo4j (Cypher) - Capsules with Python witnesses**

```cypher
MATCH (c:Capsule)-[:HAS_WITNESS]->(w:Witness {language:'python'})
RETURN c.identifier AS capsule, count(*) AS witnesses
ORDER BY witnesses DESC, capsule
```

---

## What’s included in the repo

* **Ontology**: `ontology/truthcapsule.ttl` (tiny RDFS vocabulary)
* **Shapes**: `shacl/truthcapsule.shacl.ttl` (minimal constraints)
* **Context**: `contexts/truthcapsule.context.jsonld` (JSON-LD mapping)
* **Exporter**: `scripts/export_kg.py` (YAML → Turtle + NDJSON-LD)
* **Loader**: `scripts/load_neo4j.cypher` (property-graph demo)
* **Queries**: `queries/*.sparql` (copy-paste samples)
* **Docs**: this page (`docs/KG_ONE_PAGER.md`)

Optional CI smoke: `.github/workflows/kg-smoke.yml` runs export + SHACL on every PR.

---

**Truth Capsules speak graph.** Standards-compliant RDF/SHACL + one-click Neo4j makes your policies, checks, and provenance *queryable* and *auditable*-today.
