.PHONY: help setup lint test digest digest-verify digest-reset sign verify kg compose spa spa-pages smoke keygen clean

# --- Paths & tools -----------------------------------------------------------
PY        ?= python3
VENV      ?= .venv
PYBIN     := $(VENV)/bin/python
PIP       := $(VENV)/bin/pip
ART       := artifacts/out
DOCS      := docs
SPA_OUT   ?= capsule_composer.html
TTL       := $(ART)/capsules.ttl
NDJSON    := $(ART)/capsules.ndjson
NDJSONSIG := $(ART)/capsules.signed.ndjson
CONTEXT   := contexts/truthcapsule.context.jsonld
ONTOLOGY  := ontology/truthcapsule.ttl
SHACL     := shacl/truthcapsule.shacl.ttl

# --- Help --------------------------------------------------------------------
help:
	@echo "Truth Capsules - Common Tasks"
	@echo ""
	@echo "  make setup          - Create venv and install dependencies"
	@echo "  make lint           - Lint capsules and bundles (strict checks)"
	@echo "  make test           - Run tests"
	@echo "  make digest         - Build $(NDJSON) from capsules"
	@echo "  make digest-verify  - Rebuild + verify digests"
	@echo "  make sign           - Sign $(NDJSON) -> $(NDJSONSIG) (SIGNING_KEY=...)"
	@echo "  make verify         - Verify signature (PUBLIC_KEY=...)"
	@echo "  make kg             - Export RDF/NDJSON-LD + SHACL validate"
	@echo "  make compose        - Compose example prompt+manifest"
	@echo "  make spa            - Generate SPA ($(SPA_OUT))"
	@echo "  make spa-pages      - Generate SPA to docs/index.html"
	@echo "  make smoke          - Lint → digest → sign → kg (end-to-end)"
	@echo "  make keygen         - Generate dev Ed25519 keypair in ./keys"
	@echo "  make clean          - Remove generated artifacts"

# --- Env ---------------------------------------------------------------------
setup:
	$(PY) -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt
	@echo ""
	@echo "✓ Setup complete. Activate with: source $(VENV)/bin/activate"

# --- Quality -----------------------------------------------------------------
lint:
	$(PYBIN) scripts/capsule_linter.py capsules
	$(PYBIN) scripts/bundle_linter.py bundles
	$(PYBIN) scripts/capsule_policy_check.py --bundles bundles

test:
	$(PYBIN) -m pytest -q tests

# --- Digests & signatures ----------------------------------------------------
digest:
	@mkdir -p $(ART)
	$(PYBIN) scripts/capsule_digest.py capsules --out $(NDJSON)
	@echo "✓ Digests written: $(NDJSON)"

digest-verify:
	@mkdir -p $(ART)
	$(PYBIN) scripts/capsule_digest.py capsules --out $(NDJSON) --verify
	@echo "✓ Digests rebuilt and verified"

digest-reset: digest

sign: digest
	@if [ -z "$(SIGNING_KEY)" ]; then \
		echo "Error: SIGNING_KEY not set"; \
		echo "Usage: make sign SIGNING_KEY=keys/dev.pem"; \
		exit 1; \
	fi
	$(PYBIN) scripts/capsule_sign.py \
		--in  $(NDJSON) \
		--key $(SIGNING_KEY) \
		--out $(NDJSONSIG)
	@echo "✓ Signed: $(NDJSONSIG)"

verify:
	@if [ -z "$(PUBLIC_KEY)" ]; then \
		echo "Error: PUBLIC_KEY not set"; \
		echo "Usage: make verify PUBLIC_KEY=keys/dev.pub"; \
		exit 1; \
	fi
	$(PYBIN) scripts/capsule_verify.py --in $(NDJSONSIG) --pub $(PUBLIC_KEY)

# --- Graph export ------------------------------------------------------------
kg: sign
	$(PYBIN) scripts/export_kg.py \
		--in  $(NDJSONSIG) \
		--ttl $(TTL) \
		--context $(CONTEXT) \
		--ontology $(ONTOLOGY)
	pyshacl -s $(SHACL) -m -f human $(TTL)
	@echo "✓ KG exported + SHACL validated"

# --- Compose example ---------------------------------------------------------
compose:
	@mkdir -p artifacts/composed
	$(PYBIN) scripts/compose_capsules_cli.py \
		--profile conversational \
		--bundle  conversation_red_team_baseline_v1 \
		--out      artifacts/composed/example_prompt.txt \
		--manifest artifacts/composed/example_manifest.json
	@echo "✓ Composed prompt: artifacts/composed/example_prompt.txt"

# --- SPA build ---------------------------------------------------------------
spa:
	$(PYBIN) scripts/spa/generate_spa.py --root . --output $(SPA_OUT)
	@echo "✓ Generated SPA: $(SPA_OUT)"

spa-pages:
	@mkdir -p $(DOCS)
	$(PYBIN) scripts/spa/generate_spa.py --root . --output $(DOCS)/index.html
	@echo "✓ Pages SPA: $(DOCS)/index.html"

# --- Convenience flows -------------------------------------------------------
smoke: lint digest sign kg
	@echo "✓ Smoke complete (lint → digest → sign → kg)"

keygen:
	@mkdir -p keys
	@# Dev Ed25519 keypair
	openssl genpkey -algorithm ED25519 -out keys/dev.pem
	openssl pkey -in keys/dev.pem -pubout -out keys/dev.pub
	@echo "✓ Keys: keys/dev.pem (priv), keys/dev.pub (pub)"

# --- Clean -------------------------------------------------------------------
clean:
	@rm -f  $(ART)/*.ttl $(ART)/*.ndjson $(ART)/*.json
	@rm -rf artifacts/composed
	@rm -rf .pytest_cache
	@find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	@echo "✓ Cleaned artifacts"
