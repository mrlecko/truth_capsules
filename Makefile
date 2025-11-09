.PHONY: help setup lint lint-strict test digest digest-verify digest-reset sign verify kg compose compose-bundle \
        spa spa-pages smoke keygen clean clean-venv preflight list-bundles list-profiles \
        scaffold run-witness witness-pass witness-fail witness-skip freeze

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

# --- Make settings -----------------------------------------------------------
SHELL := /bin/bash
SHELLFLAGS := -e -o pipefail -c
.DEFAULT_GOAL := help
MAKEFLAGS += --warn-undefined-variables

# --- Help --------------------------------------------------------------------
help:
	@echo "Truth Capsules - Common Tasks"
	@echo ""
	@echo "  make setup              - Create venv and install dependencies"
	@echo "  make lint               - Lint capsules and bundles"
	@echo "  make lint-strict        - Lint with strict mode"
	@echo "  make test               - Run tests"
	@echo "  make digest             - Build $(NDJSON) from capsules"
	@echo "  make digest-verify      - Rebuild + verify digests"
	@echo "  make sign               - Sign $(NDJSON) -> $(NDJSONSIG) (SIGNING_KEY=...)"
	@echo "  make verify             - Verify signature (PUBLIC_KEY=...)"
	@echo "  make kg                 - Export RDF/NDJSON-LD + SHACL validate"
	@echo "  make compose            - Compose example prompt+manifest"
	@echo "  make compose-bundle     - Compose any bundle (BUNDLE=..., PROFILE=...)"
	@echo "  make spa                - Generate SPA ($(SPA_OUT))"
	@echo "  make spa-pages          - Generate SPA to docs/index.html"
	@echo "  make spa-strict         - SPA with embedded libs (strict; fails if any missing)"
	@echo "  make spa-vendor-refresh - Refresh embedded CDN cache at $(VENDOR_DIR)"	
	@echo "  make list-bundles       - List bundles"
	@echo "  make list-profiles      - List profiles"
	@echo "  make scaffold           - Mint capsule+witness (DOMAIN, NAME, TITLE, STATEMENT, WITNESS, [FORCE=1])"
	@echo "  make run-witness        - Run a specific witness (CAP=..., WIT=..., [RUNENV='FOO=bar BAZ=qux'])"
	@echo "  make witness-pass       - Run witness with PASS fixture (CAP=..., WIT=..., INPUT_PATH=...)"
	@echo "  make witness-fail       - Run witness with FAIL fixture (CAP=..., WIT=..., INPUT_PATH=...)"
	@echo "  make witness-skip       - Run witness in SKIP mode (CAP=..., WIT=...)"
	@echo "  make smoke              - Lint → digest → sign → kg (end-to-end)"
	@echo "  make keygen             - Generate dev Ed25519 keypair in ./keys"
	@echo "  make freeze             - Freeze venv packages to requirements.txt"
	@echo "  make preflight          - Check external tools (openssl, pyshacl)"
	@echo "  make clean              - Remove generated artifacts"
	@echo "  make clean-venv         - Remove .venv"

# --- Venv bootstrap (auto) ---------------------------------------------------
$(PYBIN):
	@echo "→ Creating virtualenv at $(VENV)"
	@$(PY) -m venv $(VENV)
	@$(PIP) install -U pip
	@$(PIP) install -r requirements.txt

# --- Env ---------------------------------------------------------------------
setup:
	$(PY) -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt
	@echo ""
	@echo "✓ Setup complete. Activate with: source $(VENV)/bin/activate"

# --- Quality -----------------------------------------------------------------
lint: $(PYBIN)
	$(PYBIN) scripts/capsule_linter.py capsules
	$(PYBIN) scripts/bundle_linter.py bundles
	$(PYBIN) scripts/capsule_policy_check.py --bundles bundles

lint-strict: $(PYBIN)
	$(PYBIN) scripts/capsule_linter.py capsules --strict
	$(PYBIN) scripts/bundle_linter.py bundles --strict
	$(PYBIN) scripts/capsule_policy_check.py --bundles bundles --strict

test: $(PYBIN)
	$(PYBIN) -m pytest -q tests

# --- Digests & signatures ----------------------------------------------------
digest: $(PYBIN)
	@mkdir -p $(ART)
	$(PYBIN) scripts/capsule_digest.py capsules --out $(NDJSON)
	@echo "✓ Digests written: $(NDJSON)"

digest-verify: $(PYBIN)
	@mkdir -p $(ART)
	$(PYBIN) scripts/capsule_digest.py capsules --out $(NDJSON) --verify
	@echo "✓ Digests rebuilt and verified"

digest-reset: digest

sign: $(PYBIN) digest
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

verify: $(PYBIN)
	@if [ -z "$(PUBLIC_KEY)" ]; then \
		echo "Error: PUBLIC_KEY not set"; \
		echo "Usage: make verify PUBLIC_KEY=keys/dev.pub"; \
		exit 1; \
	fi
	$(PYBIN) scripts/capsule_verify.py --in $(NDJSONSIG) --pub $(PUBLIC_KEY)

# --- Graph export ------------------------------------------------------------
kg: $(PYBIN) sign
	$(PYBIN) scripts/export_kg.py \
		--in  $(NDJSONSIG) \
		--ttl $(TTL) \
		--context $(CONTEXT) \
		--ontology $(ONTOLOGY)
	pyshacl -s $(SHACL) -m -f human $(TTL)
	@echo "✓ KG exported + SHACL validated"

# --- Compose ---------------------------------------------------------
compose: $(PYBIN)
	@mkdir -p artifacts/composed
	$(PYBIN) scripts/compose_capsules_cli.py \
		--profile conversational \
		--bundle  conversation_red_team_baseline_v1 \
		--out      artifacts/composed/example_prompt.txt \
		--manifest artifacts/composed/example_manifest.json
	@echo "✓ Composed prompt: artifacts/composed/example_prompt.txt"

compose-bundle: $(PYBIN)
	@test -n "$(BUNDLE)"  || (echo "Error: set BUNDLE=<bundle_id>"; exit 2)
	@test -n "$(PROFILE)" || (echo "Error: set PROFILE=<profile_id>"; exit 2)
	@mkdir -p artifacts/composed
	$(PYBIN) scripts/compose_capsules_cli.py \
		--profile $(PROFILE) \
		--bundle  $(BUNDLE) \
		--out      artifacts/composed/$(BUNDLE).txt \
		--manifest artifacts/composed/$(BUNDLE).manifest.json
	@echo "✓ Composed bundle: artifacts/composed/$(BUNDLE).txt"

list-bundles: $(PYBIN)
	$(PYBIN) scripts/compose_capsules_cli.py --root . --list-bundles

list-profiles: $(PYBIN)
	$(PYBIN) scripts/compose_capsules_cli.py --root . --list-profiles

# --- SPA build ---------------------------------------------------------------
# Inline / offline SPA (single self-contained HTML)
spa:
	$(PYBIN) scripts/spa/generate_spa.py --root . --output $(SPA_OUT) --embed-cdn --vendor-dir scripts/spa/vendor
	@echo "✓ Generated SPA: $(SPA_OUT)"

# Strict offline build (fails if vendor cache missing)
spa-offline:
	$(PYBIN) scripts/spa/generate_spa.py --root . --output $(SPA_OUT) --embed-cdn --offline --vendor-dir scripts/spa/vendor
	@echo "✓ Generated SPA (offline): $(SPA_OUT)"

# Populate/refresh vendor cache (one-time, networked)
spa-vendor:
	$(PYBIN) scripts/spa/generate_spa.py --root . --output /dev/null --embed-cdn --vendor-dir scripts/spa/vendor
	@echo "✓ Cached vendor libs in scripts/spa/vendor"

spa-pages: $(PYBIN)
	@mkdir -p $(DOCS)
	$(PYBIN) scripts/spa/generate_spa.py --root . --output $(DOCS)/index.html
	@echo "✓ Pages SPA: $(DOCS)/index.html"

spa-strict:
	$(PYBIN) scripts/spa/generate_spa.py \
		--root . \
		--template scripts/spa/template.html \
		--output capsule_composer.html \
		--embed-cdn \
		--vendor-dir scripts/spa/vendor \
		--strict-embed

spa-vendor-refresh:
	rm -rf scripts/spa/vendor
	$(PYBIN) scripts/spa/generate_spa.py \
		--root . \
		--template scripts/spa/template.html \
		--output /dev/null \
		--embed-cdn \
		--vendor-dir scripts/spa/vendor


# --- Scaffolding -------------------------------------------------------------
scaffold: $(PYBIN)
	@test -x scripts/mint_witness.py || (echo "Error: scripts/mint_witness.py not found/executable"; exit 2)
	@test -n "$(DOMAIN)"   || (echo "Error: set DOMAIN=llm|pr_review|ops|..."; exit 2)
	@test -n "$(NAME)"     || (echo "Error: set NAME=<slug>"; exit 2)
	@test -n "$(TITLE)"    || (echo "Error: set TITLE='Human title'"; exit 2)
	@test -n "$(STATEMENT)"|| (echo "Error: set STATEMENT='One-sentence rule'"; exit 2)
	@test -n "$(WITNESS)"  || (echo "Error: set WITNESS=<witness_name>"; exit 2)
	$(PYBIN) scripts/mint_witness.py \
		--domain $(DOMAIN) \
		--name $(NAME) \
		--title "$(TITLE)" \
		--statement "$(STATEMENT)" \
		--witness-name $(WITNESS) \
		$(if $(FORCE),--force,)
	@echo "✓ Scaffolded capsule+witness: capsules/$(DOMAIN).$(NAME)_v1.yaml"

# --- Focused witness runs ----------------------------------------------------
# Use RUNENV to pass env, e.g. RUNENV="INPUT_PATH=artifacts/examples/foo_fail.json DOC_CLASS=opinion"
run-witness: $(PYBIN)
	@test -n "$(CAP)" || (echo "Error: set CAP=<capsule_id>"; exit 2)
	@test -n "$(WIT)" || (echo "Error: set WIT=<witness_name>"; exit 2)
	$(RUNENV) $(PYBIN) scripts/run_witnesses.py capsules --capsule $(CAP) --witness $(WIT) --json

witness-pass: $(PYBIN)
	@test -n "$(CAP)" || (echo "Error: set CAP=<capsule_id>"; exit 2)
	@test -n "$(WIT)" || (echo "Error: set WIT=<witness_name>"; exit 2)
	@test -n "$(INPUT_PATH)" || (echo "Error: set INPUT_PATH=<path_to_pass_fixture>"; exit 2)
	INPUT_PATH=$(INPUT_PATH) $(PYBIN) scripts/run_witnesses.py capsules --capsule $(CAP) --witness $(WIT) --json

witness-fail: $(PYBIN)
	@test -n "$(CAP)" || (echo "Error: set CAP=<capsule_id>"; exit 2)
	@test -n "$(WIT)" || (echo "Error: set WIT=<witness_name>"; exit 2)
	@test -n "$(INPUT_PATH)" || (echo "Error: set INPUT_PATH=<path_to_fail_fixture>"; exit 2)
	INPUT_PATH=$(INPUT_PATH) $(PYBIN) scripts/run_witnesses.py capsules --capsule $(CAP) --witness $(WIT) --json

witness-skip: $(PYBIN)
	@test -n "$(CAP)" || (echo "Error: set CAP=<capsule_id>"; exit 2)
	@test -n "$(WIT)" || (echo "Error: set WIT=<witness_name>"; exit 2)
	MODE=opinion $(PYBIN) scripts/run_witnesses.py capsules --capsule $(CAP) --witness $(WIT) --json

# --- Convenience flows -------------------------------------------------------
smoke: $(PYBIN) lint digest sign kg
	@echo "✓ Smoke complete (lint → digest → sign → kg)"

keygen:
	@mkdir -p keys
	@# Dev Ed25519 keypair
	openssl genpkey -algorithm ED25519 -out keys/dev.pem
	openssl pkey -in keys/dev.pem -pubout -out keys/dev.pub
	@echo "✓ Keys: keys/dev.pem (priv), keys/dev.pub (pub)"

freeze: $(PYBIN)
	$(PIP) freeze > requirements.txt
	@echo "✓ requirements.txt updated"

preflight:
	@command -v openssl >/dev/null || (echo "openssl not found"; exit 2)
	@command -v pyshacl >/dev/null || (echo "pyshacl not found (pip install pyshacl)"; exit 2)
	@echo "✓ Preflight OK"

# --- Clean -------------------------------------------------------------------
clean:
	@rm -f  $(ART)/*.ttl $(ART)/*.ndjson $(ART)/*.json
	@rm -rf artifacts/composed
	@rm -rf .pytest_cache
	@find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	@echo "✓ Cleaned artifacts"

clean-venv:
	@rm -rf $(VENV)
	@echo "✓ Removed $(VENV)"
