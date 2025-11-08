Awesome-here’s an **idiot-proof, copy-pasteable implementation plan** to make your Truth Capsules **“Knowledge-Graph ready”** with the **smallest** set of new files that still *wow* in 2025.

---

# 🎯 Goal (what “KG-ready” means)

From your existing YAML capsules/bundles, you can:

1. **Export** an RDF graph (Turtle) and a property-graph friendly NDJSON-LD.
2. **Validate** the RDF with **SHACL** (machine checks).
3. **Query** with a couple of ready-made **SPARQL** queries.
4. **Load** into Neo4j/Memgraph via one tiny **Cypher** demo.

You will **not** re-author capsules. The exporter reads your YAML and generates graph data.

---

# ✅ Deliverables (minimal new files)

Create these **exact** files/paths:

```
contexts/
  truthcapsule.context.jsonld

ontology/
  truthcapsule.ttl

shacl/
  truthcapsule.shacl.ttl

queries/
  list_capsules.sparql
  capsules_by_domain.sparql
  capsules_with_python_witness.sparql

scripts/
  export_kg.py
  load_neo4j.cypher

docs/
  KG_README.md
```

> Optional (nice bonus in CI): `.github/workflows/kg-smoke.yml`

---

# 📦 File contents (copy-paste)

## 1) `contexts/truthcapsule.context.jsonld`

Minimal JSON-LD context that maps your YAML keys → IRIs so RDF is automatic.

```json
{
  "@context": {
    "@vocab": "https://w3id.org/tc#",
    "id": "@id",
    "type": "@type",

    "Capsule": "Capsule",
    "Witness": "Witness",
    "Bundle": "Bundle",

    "identifier": "http://purl.org/dc/terms/identifier",
    "title": "http://purl.org/dc/terms/title",
    "statement": "statement",
    "domain": "domain",
    "version": "http://schema.org/version",
    "assumption": "assumption",

    "hasWitness": { "@id": "hasWitness", "@container": "@set" },
    "inBundle":  { "@id": "inBundle",  "@type": "@id" },

    "language": "language",
    "entrypoint": "entrypoint",
    "codeHash": "codeHash",
    "codeRef":  "codeRef",

    "author": "http://purl.org/dc/terms/creator",
    "org": "http://schema.org/affiliation",
    "license": "http://purl.org/dc/terms/license",
    "created": { "@id": "http://purl.org/dc/terms/created", "@type": "http://www.w3.org/2001/XMLSchema#dateTime" },
    "updated": { "@id": "http://purl.org/dc/terms/modified", "@type": "http://www.w3.org/2001/XMLSchema#dateTime" },

    "reviewStatus": "reviewStatus",
    "applies_to":  "applies_to",
    "dependency":  "dependency",
    "incompatible_with": "incompatible_with",
    "sensitivity": "sensitivity"
  }
}
```

## 2) `ontology/truthcapsule.ttl`

Tiny vocabulary (RDFS) + a few properties; keep it small.

```turtle
@prefix tc:   <https://w3id.org/tc#> .
@prefix dct:  <http://purl.org/dc/terms/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

tc:Capsule a rdfs:Class ; rdfs:label "Truth Capsule" .
tc:Witness a rdfs:Class ; rdfs:label "Witness (executable check)" .
tc:Bundle  a rdfs:Class ; rdfs:label "Bundle" .

tc:hasWitness a rdfs:Property ; rdfs:domain tc:Capsule ; rdfs:range tc:Witness .
tc:inBundle   a rdfs:Property ; rdfs:domain tc:Capsule ; rdfs:range tc:Bundle .
tc:statement  a rdfs:Property ; rdfs:domain tc:Capsule ; rdfs:range xsd:string .
tc:domain     a rdfs:Property ; rdfs:domain tc:Capsule ; rdfs:range xsd:string .
tc:assumption a rdfs:Property ; rdfs:domain tc:Capsule ; rdfs:range xsd:string .
tc:reviewStatus a rdfs:Property ; rdfs:domain tc:Capsule ; rdfs:range xsd:string .
tc:applies_to a rdfs:Property ; rdfs:domain tc:Capsule ; rdfs:range xsd:string .
tc:dependency a rdfs:Property ; rdfs:domain tc:Capsule ; rdfs:range xsd:string .
tc:incompatible_with a rdfs:Property ; rdfs:domain tc:Capsule ; rdfs:range xsd:string .
tc:sensitivity a rdfs:Property ; rdfs:domain tc:Capsule ; rdfs:range xsd:string .

tc:language  a rdfs:Property ; rdfs:domain tc:Witness ; rdfs:range xsd:string .
tc:entrypoint a rdfs:Property ; rdfs:domain tc:Witness ; rdfs:range xsd:string .
tc:codeHash  a rdfs:Property ; rdfs:domain tc:Witness ; rdfs:range xsd:string .
tc:codeRef   a rdfs:Property ; rdfs:domain tc:Witness ; rdfs:range xsd:anyURI .
```

## 3) `shacl/truthcapsule.shacl.ttl`

Minimal shape: Capsule must have identifier/title/statement & ≥1 witness (if witnesses exist, check language + codeHash/Ref).

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix tc: <https://w3id.org/tc#> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

tc:CapsuleShape a sh:NodeShape ;
  sh:targetClass tc:Capsule ;
  sh:property [ sh:path dct:identifier ; sh:datatype xsd:string ; sh:minCount 1 ] ;
  sh:property [ sh:path dct:title ; sh:datatype xsd:string ; sh:minCount 1 ] ;
  sh:property [ sh:path tc:statement ; sh:datatype xsd:string ; sh:minCount 1 ] ;
  sh:property [ sh:path tc:hasWitness ; sh:node tc:WitnessShape ; sh:minCount 0 ] .

tc:WitnessShape a sh:NodeShape ;
  sh:targetClass tc:Witness ;
  sh:property [ sh:path tc:language ; sh:in ("python" "node" "bash"); sh:minCount 1 ] ;
  sh:xone (
    [ sh:property [ sh:path tc:codeHash ; sh:pattern "^[a-f0-9]{64}$" ; sh:minCount 1 ] ]
    [ sh:property [ sh:path tc:codeRef  ; sh:nodeKind sh:IRI ; sh:minCount 1 ] ]
  ) .
```

## 4) `queries/list_capsules.sparql`

```sparql
PREFIX tc: <https://w3id.org/tc#>
PREFIX dct: <http://purl.org/dc/terms/>

SELECT ?capsule ?id ?title WHERE {
  ?capsule a tc:Capsule ;
           dct:identifier ?id ;
           dct:title ?title .
}
ORDER BY ?id
```

## 5) `queries/capsules_by_domain.sparql`

```sparql
PREFIX tc: <https://w3id.org/tc#>
PREFIX dct: <http://purl.org/dc/terms/>

SELECT ?domain (COUNT(?c) AS ?n) WHERE {
  ?c a tc:Capsule ; tc:domain ?domain .
}
GROUP BY ?domain
ORDER BY DESC(?n)
```

## 6) `queries/capsules_with_python_witness.sparql`

```sparql
PREFIX tc: <https://w3id.org/tc#>
PREFIX dct: <http://purl.org/dc/terms/>

SELECT DISTINCT ?id WHERE {
  ?c a tc:Capsule ; dct:identifier ?id ; tc:hasWitness ?w .
  ?w tc:language "python" .
}
ORDER BY ?id
```

## 7) `scripts/export_kg.py`

YAML → RDF (Turtle) + NDJSON-LD. Handles your schema fields, computes `codeHash` for inline `witnesses[*].code`.

```python
#!/usr/bin/env python3
import hashlib, json, pathlib, sys, yaml
from datetime import datetime
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, DCTERMS, XSD

ROOT = pathlib.Path(__file__).resolve().parents[1]
CAPS = ROOT / "capsules"
BUNDLES = ROOT / "bundles"
OUT = ROOT / "artifacts" / "out"
OUT.mkdir(parents=True, exist_ok=True)

TC = Namespace("https://w3id.org/tc#")

def norm_code(s: str) -> str:
    # Normalize for stable hashes: LF endings, no trailing spaces.
    return "\n".join(line.rstrip() for line in s.replace("\r\n", "\n").replace("\r", "\n").split("\n"))

def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

g = Graph()
g.bind("tc", TC); g.bind("dct", DCTERMS)

ndjson = []

# --- Export Capsules ---
for yml in sorted(CAPS.glob("*.yaml")):
    doc = yaml.safe_load(yml.read_text(encoding="utf-8"))
    cid = doc.get("id") or yml.stem
    c_iri = URIRef(f"https://w3id.org/tc/capsule/{cid}")
    g.add((c_iri, RDF.type, TC.Capsule))
    g.add((c_iri, DCTERMS.identifier, Literal(cid)))

    # Basic fields
    if t := doc.get("title"):     g.add((c_iri, DCTERMS.title, Literal(t)))
    if st := doc.get("statement"):g.add((c_iri, TC.statement, Literal(st)))
    if d := doc.get("domain"):    g.add((c_iri, TC.domain, Literal(d)))
    if v := doc.get("version"):   g.add((c_iri, URIRef("http://schema.org/version"), Literal(v)))
    for a in doc.get("assumptions", []):
        g.add((c_iri, TC.assumption, Literal(str(a))))

    # Provenance (minimal useful subset)
    prov = doc.get("provenance", {})
    if a := prov.get("author"):   g.add((c_iri, DCTERMS.creator, Literal(a)))
    if o := prov.get("org"):      g.add((c_iri, URIRef("http://schema.org/affiliation"), Literal(o)))
    if lic := prov.get("license"):g.add((c_iri, DCTERMS.license, Literal(lic)))
    if cr := prov.get("created"): g.add((c_iri, DCTERMS.created, Literal(cr, datatype=XSD.dateTime)))
    if up := prov.get("updated"): g.add((c_iri, DCTERMS.modified, Literal(up, datatype=XSD.dateTime)))
    if rv := prov.get("review", {}).get("status"):
        g.add((c_iri, TC.reviewStatus, Literal(rv)))

    # Arrays
    for ap in doc.get("applies_to", []):
        g.add((c_iri, TC.applies_to, Literal(ap)))
    for dep in doc.get("dependencies", []):
        g.add((c_iri, TC.dependency, Literal(dep)))
    for inc in doc.get("incompatible_with", []):
        g.add((c_iri, TC.incompatible_with, Literal(inc)))
    if sec := doc.get("security", {}):
        if s := sec.get("sensitivity"): g.add((c_iri, TC.sensitivity, Literal(s)))

    # Witnesses
    w_list = []
    for w in doc.get("witnesses", []):
        wid = w.get("name") or "w"
        w_iri = URIRef(f"{c_iri}#w/{wid}")
        g.add((w_iri, RDF.type, TC.Witness))
        g.add((c_iri, TC.hasWitness, w_iri))
        if lang := w.get("language"): g.add((w_iri, TC.language, Literal(lang)))
        if "code" in w:
            ch = sha256(norm_code(w["code"]))
            g.add((w_iri, TC.codeHash, Literal(ch)))
        if cref := (w.get("code_ref") or w.get("codeRef")):
            g.add((w_iri, TC.codeRef, URIRef(cref)))
        w_list.append({
            "@id": f"{c_iri}#w/{wid}",
            "language": w.get("language"),
            "codeHash": sha256(norm_code(w["code"])) if "code" in w else None,
            "codeRef":  w.get("code_ref") or w.get("codeRef")
        })

    ndjson.append({
        "@id": str(c_iri), "@type": "Capsule",
        "identifier": cid,
        "title": doc.get("title"),
        "statement": doc.get("statement"),
        "domain": doc.get("domain"),
        "version": doc.get("version"),
        "assumption": doc.get("assumptions", []),
        "hasWitness": w_list
    })

# --- Export Bundles (optional but nice) ---
for yml in sorted(BUNDLES.glob("*.yaml")):
    bdoc = yaml.safe_load(yml.read_text(encoding="utf-8"))
    bname = bdoc.get("name") or yml.stem
    b_iri = URIRef(f"https://w3id.org/tc/bundle/{bname}")
    g.add((b_iri, RDF.type, TC.Bundle))
    g.add((b_iri, DCTERMS.identifier, Literal(bname)))
    for cid in bdoc.get("capsules", []):
        c_iri = URIRef(f"https://w3id.org/tc/capsule/{cid}")
        # Represent membership via tc:inBundle on Capsule
        g.add((c_iri, TC.inBundle, b_iri))

# --- Write outputs ---
ttl_path = OUT / "capsules.ttl"
ndj_path = OUT / "capsules.ndjson"
g.serialize(destination=ttl_path, format="turtle")
with open(ndj_path, "w", encoding="utf-8") as f:
    for rec in ndjson:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

print(f"[KG] Wrote {ttl_path} and {ndj_path}")
```

## 8) `scripts/load_neo4j.cypher`

Property-graph demo via APOC + NDJSON (works with Neo4j, Memgraph has similar).

```cypher
CREATE CONSTRAINT capsule_pk IF NOT EXISTS FOR (c:Capsule) REQUIRE c.iri IS UNIQUE;
CREATE CONSTRAINT witness_pk IF NOT EXISTS FOR (w:Witness) REQUIRE w.iri IS UNIQUE;

CALL apoc.load.json("file:///artifacts/out/capsules.ndjson") YIELD value AS v
MERGE (c:Capsule {iri: v['@id']})
  SET c.identifier = v.identifier,
      c.title      = v.title,
      c.statement  = v.statement,
      c.domain     = v.domain,
      c.version    = v.version
WITH c, v
UNWIND coalesce(v.assumption, []) AS a
  SET c.assumptions = coalesce(c.assumptions, []) + a
WITH c, v
UNWIND coalesce(v.hasWitness, []) AS w
MERGE (wNode:Witness {iri: w['@id']})
  SET wNode.language = w.language,
      wNode.codeHash = w.codeHash,
      wNode.codeRef  = w.codeRef
MERGE (c)-[:HAS_WITNESS]->(wNode);
```

## 9) `docs/KG_README.md`

Clear, 5-minute guide.

````md
# KG Readiness Guide

## 1) Install deps
```bash
pip install rdflib pyshacl pyyaml
````

## 2) Export graph

```bash
python scripts/export_kg.py
# outputs artifacts/out/capsules.ttl and capsules.ndjson
```

## 3) Validate with SHACL

```bash
pyshacl -s shacl/truthcapsule.shacl.ttl -m -f human artifacts/out/capsules.ttl
```

## 4) Query (SPARQL)

Load `artifacts/out/capsules.ttl` into any triple store (or rdflib) and run:

* `queries/list_capsules.sparql`
* `queries/capsules_by_domain.sparql`
* `queries/capsules_with_python_witness.sparql`

## 5) Neo4j quick demo

Move `artifacts/out/capsules.ndjson` where Neo4j can read it, then run:

```
:RUN scripts/load_neo4j.cypher
```

You’ll see Capsule and Witness nodes with `HAS_WITNESS` edges.

## Notes

* `codeHash` is SHA-256 of normalized inline code (LF, trimmed lines).
* If a witness uses `codeRef`, that IRI is emitted instead of `codeHash`.

````

## 10) *(Optional)* `.github/workflows/kg-smoke.yml`
Tiny CI smoke to prove export + SHACL validate work.
```yaml
name: kg-smoke
on: [push, pull_request]
jobs:
  kg:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install rdflib pyshacl pyyaml
      - run: python scripts/export_kg.py
      - run: pyshacl -s shacl/truthcapsule.shacl.ttl -m -f human artifacts/out/capsules.ttl
````

---

# 🧭 Implementation steps (do these in order)

1. **Add directories**
   Create: `contexts/`, `ontology/`, `shacl/`, `queries/`, `docs/` if missing.

2. **Add files**
   Copy each snippet above to the exact paths.

3. **Install deps locally**

   ```bash
   pip install rdflib pyshacl pyyaml
   ```

   (Optionally add them to `requirements.txt`.)

4. **Run the exporter**

   ```bash
   python scripts/export_kg.py
   ```

   ✅ Expect:

   * `artifacts/out/capsules.ttl` (RDF/Turtle)
   * `artifacts/out/capsules.ndjson` (for Cypher/APOC)

5. **SHACL validation**

   ```bash
   pyshacl -s shacl/truthcapsule.shacl.ttl -m -f human artifacts/out/capsules.ttl
   ```

   ✅ Expect: “Conforms: True”. If not, the error will point to the bad capsule/witness.

6. **Run SPARQL (optional quick test with rdflib)**

   * Load TTL in a triplestore **or** use rdflib’s SPARQL (you can keep it manual).

7. **Neo4j demo** (optional but flashy)

   * Ensure Neo4j APOC can read `file:///artifacts/out/capsules.ndjson`.
   * In Neo4j Browser, run:

     ```
     :RUN scripts/load_neo4j.cypher
     ```

   ✅ Expect: nodes `(Capsule)` and `(Witness)`, edges `HAS_WITNESS`.

8. **(Optional) Add CI** with `kg-smoke.yml` to keep it green.

---

# 🧪 Acceptance criteria (definition of done)

* [ ] `python scripts/export_kg.py` **succeeds** and writes both files in `artifacts/out/`.
* [ ] `pyshacl ... artifacts/out/capsules.ttl` returns **Conforms: True**.
* [ ] `queries/*.sparql` return sensible results when run on the TTL.
* [ ] Neo4j Cypher loader ingests `capsules.ndjson` and shows Capsules+Witnesses.
* [ ] No changes required to existing capsule or bundle authoring workflows.

---

# 🧠 Mapping rules (so it’s unambiguous)

From your **Capsule Schema v1**:

* **IRI patterns**

  * Capsule IRI = `https://w3id.org/tc/capsule/{id}`
  * Witness IRI = `{CapsuleIRI}#w/{witness.name}`
  * Bundle IRI  = `https://w3id.org/tc/bundle/{bundle.name}`

* **Fields → RDF**

  * `id` → `dct:identifier`
  * `title` → `dct:title`
  * `statement` → `tc:statement`
  * `domain` → `tc:domain`
  * `version` → `schema:version` (as string)
  * `assumptions[]` → multiple `tc:assumption` literals
  * `provenance.author` → `dct:creator`
  * `provenance.org` → `schema:affiliation` (as literal)
  * `provenance.license` → `dct:license` (as literal for now)
  * `provenance.created|updated` → `dct:created|dct:modified` (xsd:dateTime)
  * `provenance.review.status` → `tc:reviewStatus`
  * `applies_to[]` → `tc:applies_to`
  * `dependencies[]` → `tc:dependency`
  * `incompatible_with[]` → `tc:incompatible_with`
  * `security.sensitivity` → `tc:sensitivity`
  * `witnesses[]` → `tc:hasWitness` to a `tc:Witness`.

    * `language` → `tc:language`
    * `code` → `tc:codeHash` (SHA-256 of normalized code)
    * `code_ref|codeRef` → `tc:codeRef` (IRI)

* **Bundles**

  * For each `bundles/*.yaml`, make a `tc:Bundle`.
  * For each capsule id in `capsules: [...]`, assert `tc:inBundle` from Capsule → Bundle.

---

# 🛡️ Gotchas & guardrails

* **Hash stability**: we *normalize* code before hashing (LF endings; strip trailing spaces). Your `|-` YAML style already drops final newline; good.
* **No secrets**: exporter only emits `codeHash` for inline code; it never dumps the actual code.
* **SHACL is minimal on purpose**: it won’t block capsules without witnesses; it only validates witnesses if present.
* **File paths**: exporter assumes standard repo layout (`capsules/`, `bundles/`, `artifacts/out/`). Keep that.
* **Neo4j file access**: ensure the DB can read the `artifacts/out` path (or adjust the path in Cypher).

---

# 🌟 Minimal “wow” outcome (what you can show)

* A single command **exports** a KG (`capsules.ttl`) from your YAML.
* A single command **validates** it with **SHACL** (green check).
* A **SPARQL** query lists capsules and domains.
* A **Neo4j** screenshot with Capsule ↔ Witness nodes.

That’s all you need to claim **“KG-ready”** credibly-using real standards (RDF, SHACL) and a property-graph on-ramp (Cypher) without bloating your stack.

If you want, I can also generate a one-page *“Why KG-ready matters for Truth Capsules”* explainer for your README splash.
