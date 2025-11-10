.PHONY: help setup lint lint-strict test digest digest-verify digest-reset sign verify kg compose compose-bundle \
        spa spa-pages smoke keygen clean clean-venv preflight list-bundles list-profiles \
        scaffold run-witness witness-pass witness-fail witness-skip freeze sandbox-image sandbox-smoke 

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
# Defaults to keep 'warn-undefined-variables' happy
ENV_VARS ?=
CAPSULE  ?=
WITNESS  ?=
JSON     ?= 0

# --- Make settings -----------------------------------------------------------
SHELL := /bin/bash

SHELLFLAGS := -e -o pipefail -c
.DEFAULT_GOAL := help
MAKEFLAGS += --warn-undefined-variables
.ONESHELL:

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
	@echo "  make sandbox-image      - Build sandbox image"
	@echo "  make sandbox-smoke      - Run sandbox smoke tests"
	@echo "  make witness-sandbox    - Run witness in the sandbox"


# --- Sandbox container config ------------------------------------------------
SANDBOX_ENGINE ?= docker
SANDBOX_IMAGE  ?= truthcapsules/runner:0.1
SANDBOX_USER   ?= $(shell id -u):$(shell id -g)
SANDBOX_FLAGS  ?= --rm \
                  --user $(SANDBOX_USER) \
                  --read-only \
                  --cpus=1 --memory=256m --pids-limit=64 \
                  --cap-drop=ALL --security-opt no-new-privileges \
                  --network=none \
                  --tmpfs /tmp:rw,nosuid,nodev,mode=1777,size=64m \
                  -w /work


# Resolve engine/image at make-time (empty env won't blank them out)
ENGINE := $(if $(strip $(SANDBOX_ENGINE)), $(SANDBOX_ENGINE), docker)
IMAGE  := $(if $(strip $(SANDBOX_IMAGE)), $(SANDBOX_IMAGE), truthcapsules/runner:0.1)

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

# --- Witness Execution Sandbox -----------------------------------------------

sandbox-build:
	@echo "🔧 Building sandbox image $(SANDBOX_IMAGE) ..."
	@$(SANDBOX_ENGINE) build -f container/Dockerfile.runner -t $(SANDBOX_IMAGE) .
	@echo "✓ Sandbox image built."

sandbox-image:
	@echo "🔧 Building sandbox image $(SANDBOX_IMAGE) ..."
	@$(SANDBOX_ENGINE) build -f container/Dockerfile.runner -t $(SANDBOX_IMAGE) .
	@echo "✓ Sandbox image built."

# Quick smoke: mounts /tmp/tc_wit (created here) RO at /in and runs a trivial Python witness
sandbox-smoke: sandbox-image
	@echo "🧪 Running sandbox smoke test..."
	@tmpdir="$$(mktemp -d)"; \
	  printf '%s\n' 'print("hello from sandbox")' > $$tmpdir/wit.py; \
	  $(SANDBOX_ENGINE) run $(SANDBOX_FLAGS) \
	    -v "$$tmpdir:/in:ro" \
	    -v "$$(pwd)/artifacts:/work/artifacts:ro" \
	    $(SANDBOX_IMAGE) python /in/wit.py; \
	  rc=$$?; rm -rf "$$tmpdir"; exit $$rc

# Example:
#   make witness-sandbox CAPSULE=llm.pr_risk_tags_v1 WITNESS=pr_review_covers_risks JSON=1 \
#     ENV_VARS='-e REVIEW_PATH=artifacts/examples/pr_review.md -e DIFF_PATH=artifacts/examples/pr_diff.patch'
witness-sandbox:
	@set -Eeuo pipefail

	# Make-time vars → shell vars
	ENGINE='$(SANDBOX_ENGINE)'
	IMG='$(SANDBOX_IMAGE)'

	# Optional args from make vars (expand at make time safely)
	CAPS=""
	[[ -n '$(CAPSULE)'  ]] && CAPS='--capsule $(CAPSULE)'
	WIT=""
	[[ -n '$(WITNESS)'  ]] && WIT='--witness $(WITNESS)'
	JSONF=""
	[[ '$(JSON)' = '1'  ]] && JSONF='--json'

	# ENV_VARS string -> bash array (e.g. "-e FOO=bar -e BAZ=qux")
	ENV_VARS_STR="$${ENV_VARS:-}"
	ENV_VARS_STR="$${ENV_VARS_STR%\"}"; ENV_VARS_STR="$${ENV_VARS_STR#\"}"
	ENV_VARS_STR="$${ENV_VARS_STR%\' }"; ENV_VARS_STR="$${ENV_VARS_STR#\'}"
	EV_ARR=()
	if [[ -n "$$ENV_VARS_STR" ]]; then
	  read -r -a EV_ARR <<< "$$ENV_VARS_STR"
	fi

	# Command that runs inside the container (note: python3 prefix!)
	CMD="python3 scripts/run_witnesses.py capsules $$JSONF $$CAPS $$WIT"

	echo "→ Engine : $$ENGINE"
	echo "→ Image  : $$IMG"
	echo "→ User   : $(SANDBOX_USER)"
	echo "→ Flags  : $(SANDBOX_FLAGS)"
	echo "→ Env    : $$ENV_VARS_STR"
	echo "→ Command: $$CMD"

	# Run container; capture STDOUT to OUT_JSON, mirror STDERR to our STDERR.
	set +e
	OUT_JSON="$$( "$$ENGINE" run $(SANDBOX_FLAGS) \
	  -v "$$(pwd)":/work:ro \
	  "$${EV_ARR[@]}" \
	  --entrypoint /bin/sh \
	  "$$IMG" -lc "$$CMD" 2> >(tee /dev/stderr) )"
	rc="$$?"
	set -e

	# Help if nothing came back
	if [[ -z "$$OUT_JSON" ]]; then
	  echo "[witness-sandbox] no JSON on stdout from container; check errors above" >&2
	fi

	# Contract: echo raw JSON to stdout
	printf '%s\n' "$$OUT_JSON"

	# Optional signing (non-fatal on failure)
	if [[ "$${SIGN:-0}" == "1" ]]; then
	  tmp="$$(mktemp)"
	  printf '%s' "$$OUT_JSON" > "$$tmp"
	  OUT_DIR="$${OUT_DIR:-artifacts/out}" KEY_ID="$${KEY_ID:-dev}" SIGNING_KEY="$${SIGNING_KEY:-keys/dev_ed25519_sk.pem}" \
	    python3 scripts/sign_witness.py "$$tmp" || echo "[witness-sandbox] signing failed (non-fatal)" >&2
	  rm -f "$$tmp"
	fi

		# Optional summary (nice for demos)
	if [[ -n "$$OUT_JSON" ]]; then
	  python3 - <<'PY' "$$OUT_JSON" || true
		import json,sys
		data=json.loads(sys.argv[1])
		reds=[d.get("capsule") for d in data if (d.get("status") or "").upper()=="RED"]
		greens=[d.get("capsule") for d in data if (d.get("status") or "").upper()=="GREEN"]
		print(f"[witness-sandbox] summary: GREEN={len(greens)} RED={len(reds)}")
		PY
	fi

	# Soft mode: don’t fail the shell if ALLOW_RED=1
	if [[ "$${ALLOW_RED:-0}" == "1" ]]; then
	  rc=0
	fi

	exit $$rc











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

preflight: guard-no-privkeys
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

# --- Conveniences ------------------------------------------------------------

.PHONY: keygen-dev key-fingerprint guard-no-privkeys \
        demo-cite-green demo-cite-red verify-witness-latest pages-on-docs

# Generate an Ed25519 dev pair with the names the repo already uses by default
keygen-dev:
	@mkdir -p keys
	@openssl genpkey -algorithm ED25519 -out keys/dev_ed25519_sk.pem
	@openssl pkey -in keys/dev_ed25519_sk.pem -pubout -out keys/dev_ed25519_pk.pem
	@chmod 600 keys/dev_ed25519_sk.pem
	@echo "✓ Keys written:"
	@echo "   - private: keys/dev_ed25519_sk.pem"
	@echo "   - public : keys/dev_ed25519_pk.pem"
	@echo "Set KEY_ID to an email or fingerprint, e.g.:"
	@echo "   KEY_ID="$$(git config user.email || echo demo@example.com)

# Quick fingerprints for a human KEY_ID if you prefer that over an email
key-fingerprint:
	@test -f keys/dev_ed25519_pk.pem || (echo "Missing keys/dev_ed25519_pk.pem (run make keygen-dev)"; exit 2)
	@echo "OpenSSH pub (convenient as KEY_ID):"
	@ssh-keygen -yf keys/dev_ed25519_sk.pem 2>/dev/null | awk '{print $$2}'
	@echo "SHA256 fingerprint:"
	@ssh-keygen -lf keys/dev_ed25519_pk.pem | awk '{print $$2}'

# Hard guard to avoid committing private keys by mistake
guard-no-privkeys:
	@test -z "$$(git ls-files -c -- keys/*_sk.pem 2>/dev/null)" || (echo "Refusing: a private key is tracked in git"; exit 2)

# One-line GREEN demo (signed)
demo-cite-green:
	$(MAKE) witness-sandbox CAPSULE=llm.citation_required_v1 WITNESS=citations_cover_claims JSON=1 \
	  ENV_VARS="-e ANSWER_PATH=artifacts/examples/answer_with_citation.json" \
	  SIGN=1 SIGNING_KEY=keys/dev_ed25519_sk.pem KEY_ID="$$(git config user.email || echo demo@example.com)" \
	  ALLOW_RED=1

# One-line RED demo (signed, but won't fail the shell)
demo-cite-red:
	$(MAKE) witness-sandbox CAPSULE=llm.citation_required_v1 WITNESS=citations_cover_claims JSON=1 \
	  ENV_VARS="-e ANSWER_PATH=artifacts/examples/answer_with_citation_bad.json" \
	  SIGN=1 SIGNING_KEY=keys/dev_ed25519_sk.pem KEY_ID="$$(git config user.email || echo demo@example.com)" \
	  ALLOW_RED=1

# Verify the most recent signed witness receipt using your public key
verify-witness-latest:
	@pub="$${PUBLIC_KEY:-keys/dev_ed25519_pk.pem}"; \
	f="$$(ls -1t artifacts/out/witness_*.signed.json | head -n1)"; \
	test -n "$$f" || (echo "No signed witness in artifacts/out"; exit 2); \
	echo "Verifying $$f with $$pub"; \
	$(PYBIN) scripts/verify_witness.py --in "$$f" --pub "$$pub"

# Zero-infra live demo: publish SPA as /docs/index.html (enable GitHub Pages → /docs)
pages-on-docs: spa-pages
	@echo "→ Enable GitHub Pages: Settings → Pages → 'Deploy from a branch' → /docs"
