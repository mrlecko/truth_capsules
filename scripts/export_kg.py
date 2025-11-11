#!/usr/bin/env python3
"""
Truth Capsules Knowledge Graph Exporter

Converts YAML capsules, bundles, and profiles to RDF (Turtle) and NDJSON-LD for knowledge graph integration.

Outputs:
  - artifacts/out/capsules.ttl: RDF/Turtle format for SPARQL querying
  - artifacts/out/capsules.ndjson: NDJSON-LD for property graph import (Neo4j, Memgraph)

Usage:
  python scripts/export_kg.py
"""
import hashlib
import json
import pathlib
import sys
import yaml
from datetime import datetime
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, DCTERMS, XSD

# Paths
ROOT = pathlib.Path(__file__).resolve().parents[1]
CAPS = ROOT / "capsules"
BUNDLES = ROOT / "bundles"
PROFILES = ROOT / "profiles"
OUT = ROOT / "artifacts" / "out"
OUT.mkdir(parents=True, exist_ok=True)

# Namespaces
TC = Namespace("https://w3id.org/tc#")

def norm_code(s: str) -> str:
    """Normalize code for stable hashes: LF endings, no trailing spaces."""
    return "\n".join(line.rstrip() for line in s.replace("\r\n", "\n").replace("\r", "\n").split("\n"))

def sha256(s: str) -> str:
    """Compute SHA-256 hash of string."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

# Initialize RDF graph
g = Graph()
g.bind("tc", TC)
g.bind("dct", DCTERMS)

# NDJSON-LD output list
ndjson = []

print("[KG] Loading capsules from:", CAPS)

# --- Export Capsules ---
capsule_count = 0
for yml in sorted(CAPS.glob("**/*.yaml")):
    try:
        doc = yaml.safe_load(yml.read_text(encoding="utf-8"))
        cid = doc.get("id") or yml.stem
        c_iri = URIRef(f"https://w3id.org/tc/capsule/{cid}")

        # RDF triples
        g.add((c_iri, RDF.type, TC.Capsule))
        g.add((c_iri, DCTERMS.identifier, Literal(cid)))

        # Basic fields
        if t := doc.get("title"):
            g.add((c_iri, DCTERMS.title, Literal(t)))
        if st := doc.get("statement"):
            g.add((c_iri, TC.statement, Literal(st)))
        if d := doc.get("domain"):
            g.add((c_iri, TC.domain, Literal(d)))
        if v := doc.get("version"):
            g.add((c_iri, URIRef("http://schema.org/version"), Literal(v)))

        for a in doc.get("assumptions", []):
            g.add((c_iri, TC.assumption, Literal(str(a))))

        # Provenance (minimal useful subset)
        prov = doc.get("provenance", {})
        if a := prov.get("author"):
            g.add((c_iri, DCTERMS.creator, Literal(a)))
        if o := prov.get("org"):
            g.add((c_iri, URIRef("http://schema.org/affiliation"), Literal(o)))
        if lic := prov.get("license"):
            g.add((c_iri, DCTERMS.license, Literal(lic)))
        if cr := prov.get("created"):
            g.add((c_iri, DCTERMS.created, Literal(cr, datatype=XSD.dateTime)))
        if up := prov.get("updated"):
            g.add((c_iri, DCTERMS.modified, Literal(up, datatype=XSD.dateTime)))
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
            if s := sec.get("sensitivity"):
                g.add((c_iri, TC.sensitivity, Literal(s)))

        # Witnesses
        w_list = []
        for w in doc.get("witnesses", []):
            wid = w.get("name") or "w"
            w_iri = URIRef(f"{c_iri}#w/{wid}")
            g.add((w_iri, RDF.type, TC.Witness))
            g.add((c_iri, TC.hasWitness, w_iri))

            if lang := w.get("language"):
                g.add((w_iri, TC.language, Literal(lang)))

            if "code" in w:
                ch = sha256(norm_code(w["code"]))
                g.add((w_iri, TC.codeHash, Literal(ch)))

            if cref := (w.get("code_ref") or w.get("codeRef")):
                g.add((w_iri, TC.codeRef, URIRef(cref)))

            w_list.append({
                "@id": f"{c_iri}#w/{wid}",
                "language": w.get("language"),
                "codeHash": sha256(norm_code(w["code"])) if "code" in w else None,
                "codeRef": w.get("code_ref") or w.get("codeRef")
            })

        # NDJSON-LD record
        ndjson.append({
            "@id": str(c_iri),
            "@type": "Capsule",
            "identifier": cid,
            "title": doc.get("title"),
            "statement": doc.get("statement"),
            "domain": doc.get("domain"),
            "version": doc.get("version"),
            "assumption": doc.get("assumptions", []),
            "hasWitness": w_list
        })

        capsule_count += 1

    except Exception as e:
        print(f"[KG] WARNING: Skipping {yml.name}: {e}", file=sys.stderr)

print(f"[KG] Processed {capsule_count} capsules")

# --- Export Bundles (optional but nice) ---
print("[KG] Loading bundles from:", BUNDLES)
bundle_count = 0

for yml in sorted(BUNDLES.glob("*.yaml")):
    try:
        bdoc = yaml.safe_load(yml.read_text(encoding="utf-8"))
        bname = bdoc.get("name") or yml.stem
        b_iri = URIRef(f"https://w3id.org/tc/bundle/{bname}")

        g.add((b_iri, RDF.type, TC.Bundle))
        g.add((b_iri, DCTERMS.identifier, Literal(bname)))

        capsule_ids = []
        for cid in bdoc.get("capsules", []):
            c_iri = URIRef(f"https://w3id.org/tc/capsule/{cid}")
            # Represent membership via tc:inBundle on Capsule
            g.add((c_iri, TC.inBundle, b_iri))
            capsule_ids.append(cid)

        # NDJSON-LD record
        ndjson.append({
            "@id": str(b_iri),
            "@type": "Bundle",
            "identifier": bname,
            "name": bdoc.get("name"),
            "capsules": capsule_ids
        })

        bundle_count += 1

    except Exception as e:
        print(f"[KG] WARNING: Skipping {yml.name}: {e}", file=sys.stderr)

print(f"[KG] Processed {bundle_count} bundles")

# --- Export Profiles ---
print("[KG] Loading profiles from:", PROFILES)
profile_count = 0

for yml in sorted(PROFILES.glob("*.yaml")):
    try:
        pdoc = yaml.safe_load(yml.read_text(encoding="utf-8"))
        pid = pdoc.get("id") or yml.stem
        p_iri = URIRef(f"https://w3id.org/tc/profile/{pid}")

        # RDF triples
        g.add((p_iri, RDF.type, TC.Profile))
        g.add((p_iri, DCTERMS.identifier, Literal(pid)))

        # Basic fields
        if title := pdoc.get("title"):
            g.add((p_iri, DCTERMS.title, Literal(title)))
        if desc := pdoc.get("description"):
            g.add((p_iri, DCTERMS.description, Literal(desc)))
        if ver := pdoc.get("version"):
            g.add((p_iri, URIRef("http://schema.org/version"), Literal(ver)))
        if kind := pdoc.get("kind"):
            g.add((p_iri, TC.kind, Literal(kind)))

        # Response configuration
        resp = pdoc.get("response", {})
        if fmt := resp.get("format"):
            g.add((p_iri, TC.responseFormat, Literal(fmt)))
        if policy := resp.get("policy"):
            g.add((p_iri, TC.policy, Literal(policy)))
        if sys_block := resp.get("system_block"):
            g.add((p_iri, TC.systemBlock, Literal(sys_block)))
        if footer := resp.get("footer"):
            g.add((p_iri, TC.footer, Literal(footer)))

        # Projection - capsule references
        proj = resp.get("projection", {})
        included_capsules = []
        for cref in proj.get("include", []):
            # Create relationship to capsules/bundles referenced in projection
            # These might be capsule IDs or patterns like "pedagogy.socratic"
            g.add((p_iri, TC.includesCapsule, Literal(cref)))
            included_capsules.append(cref)

        # NDJSON-LD record
        ndjson.append({
            "@id": str(p_iri),
            "@type": "Profile",
            "identifier": pid,
            "title": pdoc.get("title"),
            "description": pdoc.get("description"),
            "version": pdoc.get("version"),
            "kind": pdoc.get("kind"),
            "responseFormat": resp.get("format"),
            "includesCapsule": included_capsules
        })

        profile_count += 1

    except Exception as e:
        print(f"[KG] WARNING: Skipping {yml.name}: {e}", file=sys.stderr)

print(f"[KG] Processed {profile_count} profiles")

# --- Write outputs ---
ttl_path = OUT / "capsules.ttl"
ndj_path = OUT / "capsules.ndjson"

print("[KG] Writing Turtle to:", ttl_path)
g.serialize(destination=str(ttl_path), format="turtle")

print("[KG] Writing NDJSON-LD to:", ndj_path)
with open(ndj_path, "w", encoding="utf-8") as f:
    for rec in ndjson:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

print(f"\n[KG] ✅ Export complete!")
print(f"     Capsules: {capsule_count}")
print(f"     Bundles: {bundle_count}")
print(f"     Profiles: {profile_count}")
print(f"     RDF triples: {len(g)}")
print(f"     Output:")
print(f"       - {ttl_path}")
print(f"       - {ndj_path}")
