.PHONY: help setup lint test kg sign verify compose clean

PY=python3

help:
	@echo "Truth Capsules - Common Tasks"
	@echo ""
	@echo "  make setup      - Create venv and install dependencies"
	@echo "  make lint       - Run linter on capsules"
	@echo "  make test       - Run test suite (when available)"
	@echo "  make kg         - Export knowledge graph and validate"
	@echo "  make sign       - Sign capsules (requires SIGNING_KEY)"
	@echo "  make verify     - Verify capsule signatures"
	@echo "  make compose    - Compose example prompts from bundles"
	@echo "  make clean      - Remove generated artifacts"

setup:
	$(PY) -m venv .venv
	. .venv/bin/activate && pip install -U pip
	. .venv/bin/activate && pip install rdflib pyshacl pyyaml
	@echo ""
	@echo "✓ Setup complete. Activate with: source .venv/bin/activate"

lint:
	$(PY) scripts/capsule_linter.py capsules

test:
	@echo "Tests not yet implemented. Coming in v1.1"
	@# $(PY) -m pytest tests/

kg:
	$(PY) scripts/export_kg.py
	pyshacl -s shacl/truthcapsule.shacl.ttl -m -f human artifacts/out/capsules.ttl

sign:
	@if [ -z "$(SIGNING_KEY)" ]; then \
		echo "Error: SIGNING_KEY not set"; \
		echo "Usage: make sign SIGNING_KEY=keys/my_key.pem"; \
		exit 1; \
	fi
	$(PY) scripts/capsule_sign.py capsules --key $(SIGNING_KEY)

verify:
	$(PY) scripts/capsule_verify.py capsules

compose:
	@mkdir -p artifacts/composed
	$(PY) scripts/compose_capsules_cli.py \
		--root . \
		--profile conversational \
		--bundle conversation_red_team_baseline_v1 \
		--out artifacts/composed/example_prompt.txt \
		--manifest artifacts/composed/example_manifest.json
	@echo ""
	@echo "✓ Composed prompt: artifacts/composed/example_prompt.txt"

clean:
	rm -rf artifacts/out/*.ttl artifacts/out/*.ndjson
	rm -rf artifacts/composed/*
	rm -rf .pytest_cache __pycache__ **/__pycache__
	@echo "✓ Cleaned artifacts"
