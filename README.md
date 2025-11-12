# Truth Capsules  -  A Knowledge Architecture Example

**Demonstrator project for structured, versioned, testable LLM knowledge**

This is a reference implementation showing how I approach organizing
domain-specific knowledge for LLMs. It includes:

* **Versioned knowledge units (capsules)**
* **Pedagogy** (Socratic prompts, aphorisms)
* **Executable tests** (witnesses)
* **Composition system** (bundles, profiles)
* **Cryptographic provenance** (signing & verification)

**Status:** Demonstrator / portfolio project
**Composer Demo:** [here](https://mrlecko.github.io/truth_capsules/)

**Use Case:** Example of knowledge architecture methodology

**Author:** *mrlecko@gmail.com*  -  Intelligence Engineer & Knowledge Architect ·
**Hire me:** [Get help organizing LLM knowledge »](#hire-me)

---

## What’s inside (snapshot)

* **50 capsules** across groups  -  CI (5), Dev (8), **MacGyver (29)**,
  Support (7), Meta (1)
* **4 bundles** (`bundles/`)  -  curated compositions
* **4 profiles** (`profiles/`)  -  context-specific prompt postures
* **SPA composer**  -  single-file UI (`capsule_composer.html`)
* **Executable witnesses**  -  GREEN/RED checks + optional signatures
* **Graph tooling**  -  JSON-LD context, RDFS/Turtle ontology, SHACL,
  SPARQL & Neo4j helpers
* **Docs**  -  quickstarts, schema guides, security, CI, witnesses

> This repo is intentionally simple and self-contained to make the
> method easy to review and adapt.

---

## Why this matters

Most orgs keep prompts, policies, and “tribal knowledge” scattered in
docs and chats. **Truth Capsules** demonstrates a way to:

1. **Structure** knowledge as small, versioned units
2. **Compose** them deterministically (bundles/profiles)
3. **Test** them with executable witnesses (GREEN/RED)
4. **Prove** what ran with signed receipts

Think of it as “**knowledge you can lint, test, and ship**.”

---

## Quick tour (60 seconds)

```bash
# deps
pip install -r requirements.txt

# generate the single-file SPA composer (also powers GitHub Pages)
python scripts/spa/generate_spa.py \
  --root . \
  --output capsule_composer.html \
  --embed-cdn \
  --vendor-dir scripts/spa/vendor
```

Open `capsule_composer.html`, pick a **profile** + **bundles**, and copy
the composed prompt (manifest included).

**Witness example (GREEN/RED):**

```bash
make keygen  # one-time: writes keys/dev_ed25519_{sk,pk}.pem

# Dev: diff risk tags (no-risk vs risky patch)
make witness-sandbox CAPSULE=dev.diff_risk_tags_v1 WITNESS=diff_has_expected_risk_tags JSON=1 \
  ENV_VARS="-e DIFF_PATH=artifacts/examples/pr_diff_norisk.patch" \
  SIGN=1 SIGNING_KEY=keys/dev_ed25519_sk.pem KEY_ID=<you@org>

make witness-sandbox CAPSULE=dev.diff_risk_tags_v1 WITNESS=diff_has_expected_risk_tags JSON=1 \
  ENV_VARS="-e DIFF_PATH=artifacts/examples/pr_diff.patch" \
  SIGN=1 SIGNING_KEY=keys/dev_ed25519_sk.pem KEY_ID=<you@org> ALLOW_RED=1
```

Artifacts land in `artifacts/out/` (raw + signed receipts).

---

## Case study (mini)

**Organizing 50+ MacGyver problem-solving principles**

* **Problem:** principles scattered across notes/files; hard to inject
  into LLMs with consistency, testing, and provenance.
* **Solution:** encode each as a **capsule** (YAML + pedagogy), compose
  bundles for different contexts, and add **witnesses** to check
  application.
* **Results:** faster iteration, **reduced hallucinations** (pre-flight
  checks), and repeatable prompt builds with manifests.

---

## How it works (high level)

* **Capsules:** small YAML units with metadata + pedagogy (+ optional
  witnesses)
* **Bundles/Profiles:** deterministic composition into prompts
* **Witnesses:** executable checks (GREEN/RED) with optional signing
* **Provenance:** Ed25519 signing + verification
* **Graph:** export to RDF/Turtle & NDJSON-LD; query with SPARQL/Cypher

---

## Project structure (abridged)

```
truth_capsules/
├─ capsules/             # 50 total (CI 5, Dev 8, MacGyver 29, Support 7, Meta 1)
├─ bundles/              # 4 curated sets
├─ profiles/             # 4 context profiles
├─ artifacts/examples/   # input fixtures (GREEN/RED)
├─ artifacts/out/        # generated outputs (KG, receipts)
├─ scripts/              # CLIs (compose, run, sign, verify, export KG)
├─ capsule_composer.html # single-file SPA (also served via GitHub Pages)
└─ docs/                 # guides & references
```

---

## Not a product  -  a pattern you can adopt

This repo is a **demonstrator of method**: structure → compose →
test → prove. Copy the pattern; keep or replace any part you wish.

---

## Hire me

If you need to **turn scattered prompts/policies into structured,
versioned, testable knowledge** with provenance, I can help.

* **Prompt/Knowledge/Intelligence Architecture sprints** (1–2 weeks)
* **Capsule curation + witness design**
* **CI/Dev workflow integration** (lint/test/sign/verify)

**Contact:** *mrlecko@gmail.com* · *[linkedin](https://www.linkedin.com/in/semanticalchemist/)* ·
Calendar: *[Book a 30 minute call](https://calendly.com/mrlecko/30min)*

---

## License

MIT. Commercial use encouraged; attribution welcomed.

---

*Last updated:* 2025-11-12