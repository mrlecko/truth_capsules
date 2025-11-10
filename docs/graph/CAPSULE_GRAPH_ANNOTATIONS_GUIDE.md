# CAPSULE_GRAPH_ANNOTATIONS_GUIDE.md

**Status:** Draft v1.0
**Applies to:** Capsule Schema v1, Bundle Schema v1
**Audience:** Capsule authors, tooling developers, KG integrators
**Purpose:** Define an **optional**, backwards-compatible way to embed graph annotations inside capsule YAML that downstream exporters can use to mint RDF/SHACL and property-graph artifacts-without changing today’s authoring flow.

---

## 1. Goals & Non-Goals

### 1.1 Goals

* Allow capsule authors (or an automated “minter”) to **optionally** add semantic hints (RDF classes, relations, property-graph labels/edges) **inside** the capsule YAML.
* Keep today’s **one-way** pipeline intact: YAML → (exporter) → RDF/NDJSON-LD/Cypher.
* Ensure the annotations are **ignorable** by legacy tools and **validatable** by SHACL when used.
* Preserve **integrity**: never leak witness code; use hashes and deterministic IRIs.

### 1.2 Non-Goals

* No round-trip editing from graph back into YAML.
* No mandatory ontology commitments beyond the minimal `tc:` vocabulary (you can align more later).
* No change to the **core-content digest** definition for Capsule Schema v1.

---

## 2. Backwards Compatibility & Operating Modes

* **RC Mode (today):** Exporter **ignores** the `kg:` block if present. YAML remains the single source of truth; graph is a generated artifact.
* **Annotation Mode (later):** Exporter **merges** `kg:` hints into the emitted RDF and property-graph outputs.
* The presence/absence of `kg:` **MUST NOT** affect core validation of the capsule. It only enriches the graph outputs.

---

## 3. Terminology

* **RDF type**: An assertion of `rdf:type` (class membership), e.g., `tc:Capsule`.
* **Property-graph label**: A graph-DB node label (e.g., Neo4j label) for indexing/visual grouping.
* **Edge (property-graph)**: A labeled relationship (e.g., `(:Capsule)-[:DEPENDS_ON]->(:Capsule)`).
* **Triple (RDF)**: `(subject, predicate, object)` assertion (Turtle/SPARQL semantics).

---

## 4. IRI Patterns (Normative)

Unless explicitly overridden via `kg.iri`, the following deterministic IRIs **MUST** be used:

* **Capsule:** `https://w3id.org/tc/capsule/{id}`
* **Witness:** `{CapsuleIRI}#w/{witness.name}`
* **Bundle:** `https://w3id.org/tc/bundle/{bundle.name}`

These patterns ensure stable joins across exporters and stores.

---

## 5. YAML Extension: `kg:` Block (Optional)

The `kg:` block is **optional** at both capsule level and witness level. Tools **MUST** ignore it if unknown.

### 5.1 Capsule-level `kg` schema

```yaml
kg:
  prefixes:                # OPTIONAL. Map of CURIE prefixes to IRIs.
    tc: https://w3id.org/tc#
    dct: http://purl.org/dc/terms/
    skos: http://www.w3.org/2004/02/skos/core#
    capsule: https://w3id.org/tc/capsule/
    bundle:  https://w3id.org/tc/bundle/

  iri: "https://w3id.org/tc/capsule/{id}"   # OPTIONAL override (IRI or CURIE). Defaults to the pattern above.

  types: [ "tc:Capsule", "skos:Concept" ]   # OPTIONAL. RDF classes (IRIs or CURIEs).
  labels: [ "Capsule" ]                     # OPTIONAL. Property-graph node labels (strings).

  triples:                                   # OPTIONAL. Extra RDF assertions about this capsule.
    - p: skos:related
      o: "capsule:llm.plan_verify_answer_v1"
      o_kind: iri                           # "iri" | "literal" (default "literal")
    - p: dct:title
      o: "LLM - Citation Required"
      o_kind: literal
      datatype: xsd:string                  # OPTIONAL datatype IRI/CURIE for literals

  edges:                                     # OPTIONAL. Property-graph edges emitted in Cypher.
    - rel: IN_BUNDLE
      to: "bundle:assistant_baseline_v1"     # CURIE/IRI
      props: { strength: "required" }        # OPTIONAL small property map
    - rel: DEPENDS_ON
      to: "capsule:llm.plan_verify_answer_v1"
```

**Constraints (MUST/SHOULD):**

* `prefixes` keys **SHOULD** match `^[A-Za-z_][A-Za-z0-9_-]*$`; values **MUST** be absolute IRIs.
* `types` entries **MUST** expand to IRIs (via `prefixes` or absolute).
* `labels` entries **SHOULD** be alphanumerics/underscore only; avoid spaces for graph portability.
* `triples[*].p` and `.o` **MUST** expand to IRIs when `o_kind: iri`.
* `edges[*].to` **MUST** expand to an IRI; `rel` **SHOULD** be UPPER_SNAKE_CASE.

### 5.2 Witness-level `kg` schema

```yaml
witnesses:
  - name: five_step_gate
    language: python
    code: |-
      # ... code elided ...
    kg:                                   # OPTIONAL
      iri: "{capsule.iri}#w/five_step_gate"  # OPTIONAL override; default uses witness pattern
      types: [ "tc:Witness" ]
      labels: [ "Witness", "Python" ]
      triples:
        - p: dct:title
          o: "Five Step Gate"
          o_kind: literal
```

> **Note:** `{capsule.iri}` is an allowed template token the exporter **MAY** support to reference the computed Capsule IRI.

---

## 6. Exporter Behavior (Normative)

An exporter implementing `kg:` **MUST**:

1. **Parse** standard capsule fields as today (id, version, title, statement, domain, assumptions, provenance, witnesses, etc.).
2. **Compute canonical IRIs** per §4 unless `kg.iri` overrides them.
3. **Include base RDF** (e.g., `dct:identifier`, `dct:title`, `tc:statement`, `tc:domain`, `schema:version`, `tc:hasWitness`, etc.).
4. **Merge `kg:` annotations** if present:

   * Add `rdf:type` assertions for each entry in `kg.types`.
   * Add property-graph node **labels** in Cypher output for `kg.labels`.
   * Emit each `kg.triples` item as an RDF triple; default subject = the capsule’s IRI unless an explicit subject field is later added.
   * Emit `kg.edges` as property-graph relationships in Cypher:
     `MERGE (Capsule)-[:REL {props...}]->(Target)` where `Target` is created/merged by IRI.
5. **Witness handling**:

   * Continue to emit **`tc:codeHash`** (SHA-256 of normalized inline code) or **`tc:codeRef`** if provided.
   * Apply witness `kg:` annotations to the witness IRI (types, labels, triples).
6. **Prefix expansion**:

   * Resolve CURIEs using `kg.prefixes` **first**, then any built-in exporter defaults (e.g., `tc`, `dct`, `xsd`, `schema`, `skos`).
   * Fail validation if a CURIE cannot be expanded to an IRI.
7. **Deduplication**:

   * The exporter **SHOULD** de-duplicate emitted triples and Cypher MERGEs to avoid churn.

---

## 7. Validation & SHACL

* The base **SHACL** shapes (Capsule minima, Witness minima) continue to apply.
* When a `kg:` block is present, an **optional** SHACL “KG extension” shape **SHOULD** validate:

  * `kg.types` entries resolve to IRIs.
  * `kg.triples[*].p` resolves to IRI; if `o_kind: iri`, object resolves to IRI.
  * `kg.edges[*].to` resolves to IRI.
  * `labels` are strings that match the recommended label pattern.

*(You may ship this as `shacl/truthcapsule-kg.shacl.ttl` later; it is not required for the RC.)*

---

## 8. Integrity, Security & Digests

* The **core-content digest** (as defined today) **MUST NOT** include the `kg:` block to avoid unnecessary signature churn.
* If you need integrity on annotations, add an **optional** `provenance.signing.kg_digest` (SHA-256 over a canonical JSON of the `kg:` section).
* **Never** emit witness source code into RDF or property graphs. Only **hashes** (`tc:codeHash`) or **references** (`tc:codeRef`) are permitted.

---

## 9. Conflict Resolution

* `kg:` annotations are **additive**. They **MUST NOT** delete or mask base mappings.
* If a `kg.triples` assertion conflicts semantically with derived data, both may appear in RDF. It is the consumer’s job to reconcile.
  Exporters **SHOULD NOT** drop base triples.

---

## 10. Example (Complete)

```yaml
id: llm.citation_required_v1
version: 1.0.0
domain: llm_policies
title: "LLM - Citation Required"
statement: "Each factual claim must cite a credible source."
assumptions:
  - The environment can surface citation metadata.
provenance:
  schema: provenance.v1
  author: Jane Doe
  org: Rational OS
  license: MIT
  created: 2025-11-07T00:00:00Z
  updated: 2025-11-07T00:00:00Z
witnesses:
  - name: citation_gate
    language: python
    code: |-
      # elided…
    kg:
      labels: [ "Witness", "Python" ]
      types:  [ "tc:Witness" ]

kg:
  prefixes:
    tc: https://w3id.org/tc#
    dct: http://purl.org/dc/terms/
    skos: http://www.w3.org/2004/02/skos/core#
    capsule: https://w3id.org/tc/capsule/
    bundle:  https://w3id.org/tc/bundle/
  types: [ "tc:Capsule", "skos:Concept" ]
  labels: [ "Capsule" ]
  triples:
    - p: skos:related
      o: "capsule:llm.plan_verify_answer_v1"
      o_kind: iri
    - p: dct:title
      o: "LLM - Citation Required"
      o_kind: literal
  edges:
    - rel: IN_BUNDLE
      to: "bundle:assistant_baseline_v1"
```

**Resulting graph (informal):**

* RDF:

  * `<…/capsule/llm.citation_required_v1> rdf:type tc:Capsule, skos:Concept .`
  * `… dct:title "LLM - Citation Required" .`
  * `… skos:related <…/capsule/llm.plan_verify_answer_v1> .`
  * `… tc:hasWitness <…#w/citation_gate> .`
  * `<…#w/citation_gate> rdf:type tc:Witness ; tc:language "python" ; tc:codeHash "…" .`
* Property graph (Cypher):

  * Node `(:Capsule:CitationRequired {iri, identifier, title, …})`
  * Node `(:Witness:Python {iri, language, codeHash})`
  * Edge `(:Capsule)-[:IN_BUNDLE]->(:Bundle)`
  * Edge `(:Capsule)-[:HAS_WITNESS]->(:Witness)`

---

## 11. Versioning & Migration

* Introducing `kg:` does **not** bump Capsule Schema v1 (it’s optional).
* If you later **require** `kg:` for specific flows, bump to **`capsule_v1.1`** and document the delta.
* Exporters **SHOULD** accept capsules without `kg:` indefinitely.

---

## 12. Tooling Expectations

Exporters that implement this guide **SHOULD** provide:

* A CLI flag (default off in RC):
  `--merge-kg` (bool) → include `kg:` annotations in outputs.
* A prefixes table with safe defaults (`tc`, `dct`, `xsd`, `schema`, `skos`).
* Strict CURIE expansion with clear error messages on unknown prefixes.
* Stable hashing for witness code (normalize to LF, trim trailing spaces, ignore final newline).

---

## 13. Validation Checklist (Author)

* [ ] `kg.prefixes` includes every custom CURIE you used.
* [ ] All CURIEs resolve to **absolute IRIs**.
* [ ] `kg.types` are valid IRIs (after expansion).
* [ ] `kg.triples[*].p` is an IRI; `o` is an IRI when `o_kind: iri`.
* [ ] `kg.edges[*].to` resolves to an IRI; `rel` name is clean.
* [ ] No witness source is exposed-only `codeHash`/`codeRef`.

---

## 14. FAQ

**Q: Do I have to use `kg:` now?**
A: No. It is fully optional. The RC exporter can ignore it entirely.

**Q: Why both `types` and `labels`?**
A: `types` add standards-based RDF classes; `labels` help property-graph UX (indexing, styling).

**Q: Can I point edges to external IRIs?**
A: Yes-`edges[*].to` can be any resolvable IRI/CURIE if your prefixes cover it.

**Q: What if I want literal objects with datatypes?**
A: Use `o_kind: literal` and `datatype:` (IRI/CURIE), e.g., `xsd:string`, `xsd:dateTime`.

**Q: How do I align to PROV-O later?**
A: Add triples in `kg.triples` (e.g., provenance activities), or extend the exporter to mint named graphs for run records.

---

## 15. Summary

The `kg:` annotation block gives you a **clean, optional** path to embed semantic intent-RDF classes, cross-capsule links, graph labels/edges-while keeping the YAML authoring experience unchanged. Tools can **ignore** it today and **leverage** it tomorrow, preserving signatures, stability, and interoperability across RDF and property-graph ecosystems.
