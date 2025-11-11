# Truth Capsules Test Workflows

**Pre-Release Manual Checklist**

This document provides step-by-step workflows for testing all aspects of Truth Capsules before release. Work through each section systematically to ensure everything functions correctly.

---

## Table of Contents

1. [Initial Setup](#1-initial-setup)
2. [Minting New Components](#2-minting-new-components)
3. [Validation & Linting](#3-validation--linting)
4. [Witness Testing](#4-witness-testing)
5. [Creating Test Fixtures](#5-creating-test-fixtures)
6. [Writing Pytest Tests](#6-writing-pytest-tests)
7. [Digests & Signing](#7-digests--signing)
8. [Composition & Prompts](#8-composition--prompts)
9. [LLM Template Testing](#9-llm-template-testing)
10. [Knowledge Graph Export](#10-knowledge-graph-export)
11. [SPA Generation](#11-spa-generation)
12. [Docker Sandbox](#12-docker-sandbox)
13. [Migration Testing](#13-migration-testing)
14. [Full Smoke Test](#14-full-smoke-test)
15. [Pre-Release Checklist](#15-pre-release-checklist)

---

## 1. Initial Setup

### 1.1 Environment Setup

```bash
# Clone and navigate to repo
cd truth_capsules

# Create virtual environment
make setup

# Activate venv
source .venv/bin/activate

# Verify Python dependencies
pip list | grep -E "pyyaml|jsonschema|pytest|pyshacl"
```

**Checklist:**
- [ ] Virtual environment created
- [ ] All dependencies installed
- [ ] Python 3.8+ confirmed (`python --version`)

### 1.2 Generate Keypair (One-Time)

```bash
# Generate development Ed25519 keypair
make keygen-dev

# Verify keys exist
ls -la keys/dev_ed25519_*.pem

# Get key fingerprint
make key-fingerprint
```

**Checklist:**
- [ ] Private key: `keys/dev_ed25519_sk.pem` (600 permissions)
- [ ] Public key: `keys/dev_ed25519_pk.pem`
- [ ] Keys NOT tracked in git (check `.gitignore`)

### 1.3 Verify External Tools

```bash
# Check required tools
make preflight

# Verify Docker/Podman
docker --version || podman --version

# Verify openssl
openssl version

# Verify pyshacl
pyshacl --version
```

**Checklist:**
- [ ] `openssl` available
- [ ] `pyshacl` available
- [ ] Container engine available (Docker or Podman)
- [ ] Preflight passes

---

## 2. Minting New Components

### 2.1 Mint a New Capsule with Witness

```bash
# Example: Create a new security capsule
make scaffold \
  DOMAIN=security \
  NAME=api_rate_limit_check \
  TITLE="API Rate Limiting Enforcement" \
  STATEMENT="APIs must enforce rate limits to prevent abuse" \
  WITNESS=check_rate_limits

# Verify created file
ls -la capsules/security/api_rate_limit_check_v1.yaml
cat capsules/security/api_rate_limit_check_v1.yaml
```

**What gets created:**
- Capsule YAML at `capsules/{DOMAIN}/{NAME}_v1.yaml`
- Stub witness with Python skeleton
- Provenance metadata with your git user

**Checklist:**
- [ ] Capsule file created with correct ID format
- [ ] Witness code section present
- [ ] Provenance fields populated
- [ ] File in correct domain subdirectory

### 2.2 Customize the Witness Code

Edit the generated capsule and replace the witness code:

```python
# Example witness implementation
import os
import sys
import json

def main():
    # Get input from env var
    config_path = os.getenv("API_CONFIG_PATH")
    if not config_path:
        print("ERROR: API_CONFIG_PATH not set", file=sys.stderr)
        sys.exit(2)

    # Load and check config
    with open(config_path) as f:
        config = json.load(f)

    rate_limit = config.get("rate_limit")

    # Test the statement
    if rate_limit and rate_limit.get("enabled"):
        print("PASS: Rate limiting enabled")
        sys.exit(0)
    else:
        print("FAIL: Rate limiting not configured")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**Checklist:**
- [ ] Witness uses env vars for inputs (not hardcoded paths)
- [ ] Exit codes: 0 (PASS), 1 (FAIL), 2 (ERROR), 3 (SKIP)
- [ ] Clear output messages
- [ ] Error handling for missing inputs

### 2.3 Mint a New Profile

```bash
# Create a new profile for a specific use case
make mint-profile \
  PROFILE_NAME=security_audit_v1 \
  PROFILE_TITLE="Security Audit Assistant" \
  PROFILE_DESC="Profile optimized for security auditing tasks"

# Verify created
ls -la profiles/security_audit_v1.yaml
```

**Edit the profile** (`profiles/security_audit_v1.yaml`):

```yaml
kind: profile
id: profile.security_audit_v1
title: Security Audit Assistant
version: 1.0.0
description: Profile optimized for security auditing tasks

response:
  format: natural
  override_compose_defaults: true
  force_pedagogy: true

  fragments:
    - id: system
      kind: system
      include: true
      content: |
        You are a security audit assistant. Focus on:
        - Identifying security vulnerabilities
        - Verifying security controls
        - Providing remediation guidance

  capsules_heading: "Security Guidelines"

  projection:
    include:
      - pedagogy.socratic
      - pedagogy.aphorisms
    render:
      capsule_header: "{title}: {statement}"

download:
  suggested_ext: txt
```

**Checklist:**
- [ ] Profile file created with correct structure
- [ ] `kind: profile` field present
- [ ] Unique profile ID
- [ ] Response format configured
- [ ] Fragments defined

### 2.4 Create a New Bundle

Create `bundles/security_audit_v1.yaml`:

```yaml
name: security_audit_v1_bundle
version: 1.0.0
description: Security audit capsule bundle
applies_to:
  - security_audit
  - code_review
capsules:
  - security.api_rate_limit_check_v1
  - ci.secrets_in_build_env_v1
  - ci.container_hardening_v1
  - dev.secret_scan_baseline_v1
excludes: []
priority_overrides:
  security.api_rate_limit_check_v1: 100
order:
  - security.api_rate_limit_check_v1
  - ci.secrets_in_build_env_v1
  - ci.container_hardening_v1
  - dev.secret_scan_baseline_v1
tags:
  - security
  - audit
notes: |
  Security-focused bundle for audit workflows.
```

**Checklist:**
- [ ] Bundle name follows convention: `{name}_v{N}_bundle`
- [ ] Version semantic (1.0.0)
- [ ] Capsule IDs match actual capsules
- [ ] Priority and order defined
- [ ] Tags for discoverability

### 2.5 Create a New LLM Template

Create `llm_templates/custom_model.yaml`:

```yaml
id: custom_model_chat
label: "Custom: My Model (chat)"
model: "custom-model-name"
description: "Chat completion for custom model"
engine: "llm"
input_mode: "arg"
extra_flags: []
cmd_template: |
  {{SYS_HEREDOC}}
  llm -m {{MODEL}} --system "$TC_SYSTEM" {{EXTRA_FLAGS}} {{INPUT_FRAGMENT}}
```

**Template variables available:**
- `{{MODEL}}` - Model name from `model` field
- `{{SYS_HEREDOC}}` - System prompt heredoc wrapper
- `{{EXTRA_FLAGS}}` - Additional flags
- `{{INPUT_FRAGMENT}}` - User input handling

**Checklist:**
- [ ] Unique template ID
- [ ] Clear label for UI display
- [ ] Model name specified
- [ ] Engine type set (`llm`, `openai`, etc.)
- [ ] Command template uses proper variables

---

## 3. Validation & Linting

### 3.1 Basic Linting

```bash
# Lint all capsules
make lint

# Expected output: capsule count, error count, warning count
```

**Checklist:**
- [ ] No errors reported
- [ ] Warnings reviewed and acceptable
- [ ] All capsules parsed successfully

### 3.2 Strict Linting

```bash
# Strict mode (requires approved review status)
make lint-strict

# This may fail for draft capsules - that's expected
```

**Checklist:**
- [ ] Production capsules pass strict mode
- [ ] Draft capsules properly marked
- [ ] Review status fields present

### 3.3 Schema Validation

```bash
# Validate against JSON Schema
make lint-schema SCHEMA=schemas/capsule.schema.v1.json

# Check specific capsule
python scripts/capsule_linter.py \
  capsules/security/api_rate_limit_check_v1.yaml \
  --schema schemas/capsule.schema.v1.json
```

**Checklist:**
- [ ] All required fields present
- [ ] Field types match schema
- [ ] Nested structures valid
- [ ] No schema violations

### 3.4 Bundle Linting

```bash
# Lint all bundles
python scripts/bundle_linter.py bundles

# Check specific bundle
python scripts/bundle_linter.py bundles/security_audit_v1.yaml
```

**Checklist:**
- [ ] All referenced capsules exist
- [ ] No circular dependencies
- [ ] Bundle metadata valid

---

## 4. Witness Testing

### 4.1 Local Witness Execution

```bash
# Run a specific witness locally
make run-witness \
  CAP=security.api_rate_limit_check_v1 \
  WIT=check_rate_limits \
  RUNENV="API_CONFIG_PATH=artifacts/examples/api_config.json"

# Check exit code
echo $?
# 0 = PASS, 1 = FAIL, 2 = ERROR, 3 = SKIP
```

**Checklist:**
- [ ] Witness executes without errors
- [ ] Correct exit code returned
- [ ] Output messages clear
- [ ] Environment variables handled correctly

### 4.2 Test PASS Scenario

Create fixture: `artifacts/examples/api_config_pass.json`

```json
{
  "rate_limit": {
    "enabled": true,
    "requests_per_minute": 100
  }
}
```

```bash
# Test PASS case
make witness-pass \
  CAP=security.api_rate_limit_check_v1 \
  WIT=check_rate_limits \
  INPUT_PATH=artifacts/examples/api_config_pass.json
```

**Checklist:**
- [ ] Exit code 0 (PASS)
- [ ] "PASS" in output
- [ ] JSON output valid

### 4.3 Test FAIL Scenario

Create fixture: `artifacts/examples/api_config_fail.json`

```json
{
  "rate_limit": {
    "enabled": false
  }
}
```

```bash
# Test FAIL case
make witness-fail \
  CAP=security.api_rate_limit_check_v1 \
  WIT=check_rate_limits \
  INPUT_PATH=artifacts/examples/api_config_fail.json
```

**Checklist:**
- [ ] Exit code 1 (FAIL)
- [ ] "FAIL" in output
- [ ] JSON output valid

### 4.4 Test SKIP Scenario

```bash
# Test SKIP case (opinion mode)
make witness-skip \
  CAP=security.api_rate_limit_check_v1 \
  WIT=check_rate_limits
```

**Checklist:**
- [ ] Exit code 3 (SKIP)
- [ ] "SKIP" in output
- [ ] JSON output valid

---

## 5. Creating Test Fixtures

### 5.1 Fixture Directory Structure

```bash
# Organize fixtures by domain
mkdir -p artifacts/examples/{security,ci,dev,support}

# Create fixture files with clear naming
# Format: {domain}/{test_case}_{pass|fail}.{ext}
```

**Example fixtures:**

`artifacts/examples/security/api_config_pass.json`:
```json
{
  "rate_limit": {"enabled": true, "requests_per_minute": 100},
  "auth": {"method": "jwt", "expiry": 3600}
}
```

`artifacts/examples/security/api_config_fail.json`:
```json
{
  "rate_limit": {"enabled": false},
  "auth": null
}
```

**Checklist:**
- [ ] Fixtures organized by domain
- [ ] Clear naming convention (pass/fail suffix)
- [ ] Both positive and negative test cases
- [ ] Valid file formats (JSON, YAML, TXT, etc.)
- [ ] Realistic test data

### 5.2 Document Fixture Requirements

Create `artifacts/examples/security/README.md`:

```markdown
# Security Test Fixtures

## api_config_pass.json
Valid API configuration with rate limiting enabled.

Required fields:
- `rate_limit.enabled`: true
- `rate_limit.requests_per_minute`: positive integer

## api_config_fail.json
Invalid API configuration without rate limiting.

Expected to trigger FAIL status.
```

**Checklist:**
- [ ] Each fixture documented
- [ ] Required fields listed
- [ ] Expected behavior noted

---

## 6. Writing Pytest Tests

### 6.1 Add Test to test_demo_witnesses.py

Edit `tests/test_demo_witnesses.py`:

```python
# Add helper function for env vars
def _env_security_rate_limit():
    return {"API_CONFIG_PATH": "artifacts/examples/security/api_config_pass.json"}

# Add test function
def test_security_api_rate_limit():
    """Test API rate limiting check witness"""
    data = _run_make(
        "security.api_rate_limit_check_v1",
        "check_rate_limits",
        _env_security_rate_limit()
    )
    _assert_capsule_status(data, "GREEN")

# Test FAIL case with parametrize
@pytest.mark.parametrize("all_green", [True, False])
def test_security_api_rate_limit_scenarios(all_green):
    """Test both PASS and FAIL scenarios"""
    env = {
        "API_CONFIG_PATH": (
            "artifacts/examples/security/api_config_pass.json"
            if all_green else
            "artifacts/examples/security/api_config_fail.json"
        )
    }
    data = _run_make("security.api_rate_limit_check_v1", "check_rate_limits", env)
    expected = "GREEN" if all_green else "RED"
    _assert_capsule_status(data, expected)
```

**Checklist:**
- [ ] Helper function for env vars
- [ ] Test function with clear name
- [ ] Uses `_run_make` helper
- [ ] Asserts expected status
- [ ] Both scenarios tested (if applicable)

### 6.2 Run Tests

```bash
# Run all tests
make test

# Run specific test
pytest tests/test_demo_witnesses.py::test_security_api_rate_limit -v

# Run with coverage
pytest --cov=scripts tests/
```

**Checklist:**
- [ ] All tests pass
- [ ] No skipped tests (unless intentional)
- [ ] Coverage adequate for new code
- [ ] Test output clear

### 6.3 Add Conftest Fixtures (if needed)

Edit `tests/conftest.py`:

```python
import pytest

@pytest.fixture
def all_green(request):
    """Parametrize tests with GREEN/RED scenarios"""
    return request.param if hasattr(request, "param") else True

@pytest.fixture
def api_config_fixture(tmp_path):
    """Create temporary API config fixture"""
    config_file = tmp_path / "api_config.json"
    config_file.write_text('{"rate_limit": {"enabled": true}}')
    return str(config_file)
```

**Checklist:**
- [ ] Fixtures reusable across tests
- [ ] Temporary files cleaned up
- [ ] Clear fixture documentation

---

## 7. Digests & Signing

### 7.1 Generate Capsule Digests

```bash
# Generate NDJSON digest of all capsules
make digest

# Output: artifacts/out/capsules.ndjson
cat artifacts/out/capsules.ndjson | jq -s 'length'
```

**Checklist:**
- [ ] NDJSON file created
- [ ] One line per capsule
- [ ] Valid JSON on each line
- [ ] Digest fields present (sha256)

### 7.2 Verify Digests

```bash
# Rebuild digests and verify they match
make digest-verify

# Should confirm: "✓ Digests rebuilt and verified"
```

**Checklist:**
- [ ] Digest verification passes
- [ ] No mismatches reported
- [ ] Deterministic digests (run twice, compare)

### 7.3 Sign Capsule Digest

```bash
# Sign the digest file with your key
make sign SIGNING_KEY=keys/dev_ed25519_sk.pem

# Output: artifacts/out/capsules.signed.ndjson
head -1 artifacts/out/capsules.signed.ndjson | jq .proof
```

**Expected proof structure:**
```json
{
  "type": "Ed25519",
  "created": "2025-01-11T14:30:00Z",
  "keyId": "user@example.com",
  "canonical": {
    "algorithm": "sha256",
    "hash": "...",
    "digest": "..."
  },
  "signature": "base64_signature..."
}
```

**Checklist:**
- [ ] Signed file created
- [ ] Proof object present on each line
- [ ] Signature is base64 encoded
- [ ] KeyId populated
- [ ] Canonical digest present

### 7.4 Verify Signature

```bash
# Verify signed digest with public key
make verify PUBLIC_KEY=keys/dev_ed25519_pk.pem

# Should confirm: "✓ All signatures valid"
```

**Checklist:**
- [ ] Signature verification passes
- [ ] No invalid signatures
- [ ] KeyId matches expectations

### 7.5 Test Witness Signing

```bash
# Run witness with signing enabled
make witness-sandbox \
  CAPSULE=security.api_rate_limit_check_v1 \
  WITNESS=check_rate_limits \
  JSON=1 \
  ENV_VARS="-e API_CONFIG_PATH=artifacts/examples/security/api_config_pass.json" \
  SIGN=1 \
  SIGNING_KEY=keys/dev_ed25519_sk.pem \
  KEY_ID="$(git config user.email)"

# Check signed witness receipt
ls -lt artifacts/out/witness_*.signed.json | head -1
cat $(ls -t artifacts/out/witness_*.signed.json | head -1) | jq .proof
```

**Checklist:**
- [ ] Signed witness receipt created
- [ ] Proof object in receipt
- [ ] Timestamp present
- [ ] Signature valid

### 7.6 Verify Witness Signature

```bash
# Verify most recent witness receipt
make verify-witness-latest PUBLIC_KEY=keys/dev_ed25519_pk.pem

# Or verify specific receipt
python scripts/verify_witness.py \
  --in artifacts/out/witness_20250111T143000Z.signed.json \
  --pub keys/dev_ed25519_pk.pem
```

**Checklist:**
- [ ] Witness signature valid
- [ ] Timestamp within acceptable range
- [ ] KeyId matches expected signer

---

## 8. Composition & Prompts

### 8.1 List Available Bundles

```bash
# List all bundles
make list-bundles

# Expected output: bundle names and descriptions
```

**Checklist:**
- [ ] All bundles listed
- [ ] New bundle appears in list
- [ ] Descriptions clear

### 8.2 List Available Profiles

```bash
# List all profiles
make list-profiles

# Expected output: profile names and descriptions
```

**Checklist:**
- [ ] All profiles listed
- [ ] New profile appears in list
- [ ] Descriptions clear

### 8.3 Compose a Prompt

```bash
# Compose using profile + bundle
make compose-bundle \
  PROFILE=security_audit_v1 \
  BUNDLE=security_audit_v1_bundle

# Output: artifacts/composed/security_audit_v1_bundle.txt
#         artifacts/composed/security_audit_v1_bundle.manifest.json

# Review prompt
cat artifacts/composed/security_audit_v1_bundle.txt
```

**Checklist:**
- [ ] Prompt file generated
- [ ] Manifest file generated
- [ ] Capsules included in expected order
- [ ] Pedagogy sections rendered correctly
- [ ] Profile fragments present
- [ ] No placeholder text remaining

### 8.4 Validate Manifest

```bash
# Check manifest structure
cat artifacts/composed/security_audit_v1_bundle.manifest.json | jq .

# Expected fields:
# - composed_at (timestamp)
# - profile
# - bundle
# - capsules[] (array of capsule IDs)
# - capsule_count
```

**Checklist:**
- [ ] Valid JSON
- [ ] All expected fields present
- [ ] Capsule count matches bundle
- [ ] Timestamp recent

### 8.5 Test Default Composition

```bash
# Test default example composition
make compose

# Output: artifacts/composed/example_prompt.txt
cat artifacts/composed/example_prompt.txt
```

**Checklist:**
- [ ] Default composition works
- [ ] No errors in output
- [ ] Prompt readable and structured

---

## 9. LLM Template Testing

### 9.1 Test Template Rendering

```bash
# Manually test template variable expansion
python scripts/compose_capsules_cli.py \
  --root . \
  --profile security_audit_v1 \
  --bundle security_audit_v1_bundle \
  --llm-template custom_model_chat \
  --out artifacts/composed/test_prompt.txt

# Check rendered command
cat artifacts/composed/test_prompt.txt
```

**Checklist:**
- [ ] Template variables resolved
- [ ] System prompt properly formatted
- [ ] Command structure valid
- [ ] No unresolved `{{variables}}`

### 9.2 Test with Multiple Templates

Test each LLM template:

```bash
# OpenAI GPT-4o
make compose-bundle \
  PROFILE=security_audit_v1 \
  BUNDLE=security_audit_v1_bundle

# Anthropic Claude
python scripts/compose_capsules_cli.py \
  --profile security_audit_v1 \
  --bundle security_audit_v1_bundle \
  --llm-template anthropic_sonnet_chat \
  --out artifacts/composed/claude_test.txt

# Local Ollama
python scripts/compose_capsules_cli.py \
  --profile security_audit_v1 \
  --bundle security_audit_v1_bundle \
  --llm-template ollama_llama3_local \
  --out artifacts/composed/ollama_test.txt
```

**Checklist:**
- [ ] OpenAI template works
- [ ] Anthropic template works
- [ ] Ollama template works
- [ ] Custom template works
- [ ] Each produces valid command

### 9.3 Test Template in SPA

```bash
# Generate SPA
make spa

# Open in browser
# Check that LLM template dropdown includes new template
```

**Checklist:**
- [ ] New template appears in dropdown
- [ ] Template selection changes command output
- [ ] Copy button works
- [ ] No JavaScript errors

---

## 10. Knowledge Graph Export

### 10.1 Export to RDF/TTL

```bash
# Export knowledge graph with SHACL validation
make kg

# Outputs:
# - artifacts/out/capsules.ttl (RDF Turtle)
# - SHACL validation report
```

**Checklist:**
- [ ] TTL file created
- [ ] SHACL validation passes
- [ ] No constraint violations
- [ ] File is valid RDF

### 10.2 Validate TTL Manually

```bash
# Parse TTL file with rapper (if available)
rapper -i turtle -o ntriples artifacts/out/capsules.ttl > /dev/null

# Or use Python rdflib
python -c "
from rdflib import Graph
g = Graph()
g.parse('artifacts/out/capsules.ttl', format='turtle')
print(f'Loaded {len(g)} triples')
"
```

**Checklist:**
- [ ] TTL parses without errors
- [ ] Triple count reasonable
- [ ] Ontology terms used correctly

### 10.3 Test SHACL Validation

```bash
# Run SHACL validation explicitly
pyshacl \
  -s shacl/truthcapsule.shacl.ttl \
  -m -f human \
  artifacts/out/capsules.ttl

# Should output: "Validation Report: Conforms: True"
```

**Checklist:**
- [ ] SHACL validation passes
- [ ] No shape violations
- [ ] All required properties present

### 10.4 Load into Neo4j (Optional)

If you have Neo4j running:

```bash
# Start Neo4j
./scripts/dev_neo4j_demo.sh

# Load Cypher script
cypher-shell -u neo4j -p password < scripts/load_neo4j.cypher

# Or use the export script
python scripts/export_kg.py \
  --in artifacts/out/capsules.signed.ndjson \
  --ttl artifacts/out/capsules.ttl \
  --context contexts/truthcapsule.context.jsonld \
  --ontology ontology/truthcapsule.ttl
```

**Checklist:**
- [ ] Neo4j accepts data
- [ ] Nodes created for capsules
- [ ] Relationships established
- [ ] Query interface works

### 10.5 Verify Graph Structure

Query the graph:

```bash
# Count capsules
echo 'MATCH (c:Capsule) RETURN count(c)' | cypher-shell -u neo4j -p password

# List domains
echo 'MATCH (c:Capsule) RETURN DISTINCT c.domain' | cypher-shell -u neo4j -p password

# Check relationships
echo 'MATCH (c:Capsule)-[r]->() RETURN type(r), count(r)' | cypher-shell -u neo4j -p password
```

**Checklist:**
- [ ] Capsule count correct
- [ ] Domains match expectation
- [ ] Relationships present
- [ ] No orphaned nodes

---

## 11. SPA Generation

### 11.1 Generate Basic SPA

```bash
# Generate single-page app
make spa

# Output: capsule_composer.html
ls -lh capsule_composer.html
```

**Checklist:**
- [ ] HTML file created
- [ ] File size reasonable (< 5MB typically)
- [ ] No build errors

### 11.2 Test SPA in Browser

```bash
# Open in default browser
open capsule_composer.html  # macOS
xdg-open capsule_composer.html  # Linux
start capsule_composer.html  # Windows
```

**Manual testing checklist:**
- [ ] Page loads without errors
- [ ] Profile dropdown populated
- [ ] Bundle dropdown populated
- [ ] LLM template dropdown populated
- [ ] Compose button works
- [ ] Prompt rendered correctly
- [ ] Copy button works
- [ ] Download button works
- [ ] Manifest tab shows JSON
- [ ] No console errors (F12)

### 11.3 Generate Offline SPA

```bash
# Generate offline SPA with embedded libs
make spa-offline

# Or refresh vendor cache first
make spa-vendor-refresh
make spa-offline
```

**Checklist:**
- [ ] Offline SPA generated
- [ ] All CDN resources embedded
- [ ] Works without internet (disable network, refresh)
- [ ] File size larger but complete

### 11.4 Generate Pages SPA

```bash
# Generate for GitHub Pages
make spa-pages

# Output: docs/index.html
ls -lh docs/index.html
```

**Checklist:**
- [ ] File in docs/ directory
- [ ] Suitable for GitHub Pages
- [ ] All functionality works

### 11.5 Test Embedding

Create `test_embed.html`:

```html
<!DOCTYPE html>
<html>
<head><title>Embed Test</title></head>
<body>
  <h1>Truth Capsules Embedded</h1>
  <iframe src="capsule_composer.html" width="100%" height="800px"></iframe>
</body>
</html>
```

**Checklist:**
- [ ] SPA embeds in iframe
- [ ] Functionality preserved
- [ ] No CORS errors

---

## 12. Docker Sandbox

### 12.1 Build Sandbox Image

```bash
# Build Docker image
make sandbox-image

# Verify image exists
docker images | grep truthcapsules/runner
```

**Checklist:**
- [ ] Image builds successfully
- [ ] No build errors
- [ ] Image tagged correctly

### 12.2 Run Sandbox Smoke Test

```bash
# Quick smoke test
make sandbox-smoke

# Should output: "hello from sandbox"
```

**Checklist:**
- [ ] Smoke test passes
- [ ] Container runs and exits cleanly
- [ ] Output captured correctly

### 12.3 Test Witness in Sandbox

```bash
# Run witness in isolated container
make witness-sandbox \
  CAPSULE=security.api_rate_limit_check_v1 \
  WITNESS=check_rate_limits \
  JSON=1 \
  ENV_VARS="-e API_CONFIG_PATH=artifacts/examples/security/api_config_pass.json"

# Check result
echo $?  # Should be 0 for GREEN
```

**Checklist:**
- [ ] Witness executes in container
- [ ] JSON output returned
- [ ] Exit code correct
- [ ] No container errors

### 12.4 Verify Sandbox Isolation

```bash
# Test read-only filesystem
make witness-sandbox \
  CAPSULE=meta.truth_capsules_v1 \
  WITNESS=canonical_digest_demo \
  JSON=1

# Container should have:
# - Read-only root filesystem
# - No network access
# - Limited CPU/memory
# - tmpfs for /tmp only
```

**Checklist:**
- [ ] Read-only filesystem enforced
- [ ] Network disabled (--network=none)
- [ ] Resource limits applied
- [ ] Tmpfs writable, limited size

### 12.5 Test Sandbox with Signed Witness

```bash
# Run with signing in sandbox
make demo-cite-green

# Or custom:
make witness-sandbox \
  CAPSULE=security.api_rate_limit_check_v1 \
  WITNESS=check_rate_limits \
  JSON=1 \
  ENV_VARS="-e API_CONFIG_PATH=artifacts/examples/security/api_config_pass.json" \
  SIGN=1 \
  SIGNING_KEY=keys/dev_ed25519_sk.pem \
  KEY_ID="$(git config user.email)"

# Verify signed receipt created
ls -lt artifacts/out/witness_*.signed.json | head -1
```

**Checklist:**
- [ ] Witness runs in sandbox
- [ ] Signing applied after execution
- [ ] Signed receipt created
- [ ] Signature valid

---

## 13. Migration Testing

### 13.1 Create Test Schema

Create `schemas/capsule.schema.v2.json` (test schema):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Truth Capsule v2.0",
  "type": "object",
  "required": ["id", "version", "domain", "statement", "new_field"],
  "properties": {
    "new_field": {
      "type": "string",
      "description": "New required field in v2"
    }
  }
}
```

### 13.2 Create Migration Rules

Create `schemas/v1_to_v2_test_rules.json`:

```json
{
  "description": "Test migration v1.0 to v2.0",
  "from_version": "v1.0",
  "to_version": "v2.0",
  "rules": [
    {
      "type": "add_field",
      "params": {
        "path": "new_field",
        "value": "default_value"
      }
    }
  ]
}
```

### 13.3 Test Dry Run Migration

```bash
# Preview migration without changes
make migrate \
  TARGET=capsules/security/api_rate_limit_check_v1.yaml \
  MIGRATION_RULES=schemas/v1_to_v2_test_rules.json \
  DRY_RUN=1

# Review changes shown
```

**Checklist:**
- [ ] Dry run shows expected changes
- [ ] No files modified
- [ ] Changes are correct
- [ ] No errors in dry run

### 13.4 Test Live Migration (Single File)

```bash
# Create backup first
cp capsules/security/api_rate_limit_check_v1.yaml \
   capsules/security/api_rate_limit_check_v1.yaml.manual_backup

# Migrate single file
make migrate \
  TARGET=capsules/security/api_rate_limit_check_v1.yaml \
  MIGRATION_RULES=schemas/v1_to_v2_test_rules.json

# Check automatic backup created
ls -lt capsules/security/*.backup.*

# Verify changes
cat capsules/security/api_rate_limit_check_v1.yaml | grep new_field
```

**Checklist:**
- [ ] Migration succeeds
- [ ] Automatic backup created
- [ ] New field added
- [ ] File still valid YAML
- [ ] Can restore from backup

### 13.5 Test Restore

```bash
# Restore from backup
cp capsules/security/api_rate_limit_check_v1.yaml.manual_backup \
   capsules/security/api_rate_limit_check_v1.yaml

# Verify restored
cat capsules/security/api_rate_limit_check_v1.yaml | grep -c new_field
# Should output: 0
```

**Checklist:**
- [ ] Restore successful
- [ ] File back to original state
- [ ] No corruption

### 13.6 Test Directory Migration

```bash
# Migrate entire domain (dry run first)
make migrate-dir \
  DIR=capsules/security \
  MIGRATION_RULES=schemas/v1_to_v2_test_rules.json \
  DRY_RUN=1

# Review all changes, then run live if good
```

**Checklist:**
- [ ] All capsules in directory migrated
- [ ] Backups created for each
- [ ] No failures reported

### 13.7 Validate Post-Migration

```bash
# Lint migrated capsules
make lint

# Validate against new schema (if defined)
make lint-schema SCHEMA=schemas/capsule.schema.v2.json
```

**Checklist:**
- [ ] Migrated capsules pass linting
- [ ] Schema validation passes
- [ ] No new errors introduced

---

## 14. Full Smoke Test

### 14.1 Run Complete Smoke Test

```bash
# Full pipeline: lint → digest → sign → kg
make smoke

# This runs:
# 1. Lint all capsules and bundles
# 2. Generate digests
# 3. Sign digests
# 4. Export to knowledge graph
# 5. SHACL validation
```

**Expected output:**
```
✓ Capsules: 25  errors: 0  warnings: 3
✓ Bundles: 4   errors: 0  warnings: 0
✓ Digests written: artifacts/out/capsules.ndjson
✓ Signed: artifacts/out/capsules.signed.ndjson
✓ KG exported + SHACL validated
✓ Smoke complete (lint → digest → sign → kg)
```

**Checklist:**
- [ ] All lint checks pass
- [ ] Digests generated
- [ ] Signing succeeds
- [ ] KG export succeeds
- [ ] SHACL validation passes
- [ ] No errors in pipeline

### 14.2 Run Test Suite

```bash
# Run all pytest tests
make test

# Run with verbose output
pytest -v tests/

# Run specific test file
pytest tests/test_demo_witnesses.py -v
```

**Checklist:**
- [ ] All tests pass
- [ ] No skipped tests (unless intentional)
- [ ] No warnings
- [ ] Test coverage adequate

### 14.3 Test End-to-End Workflow

Full workflow from creation to verification:

```bash
# 1. Create new capsule
make scaffold \
  DOMAIN=test \
  NAME=e2e_demo \
  TITLE="End-to-End Demo" \
  STATEMENT="E2E workflow test" \
  WITNESS=e2e_check

# 2. Edit witness code (make it pass)
# Edit capsules/test/e2e_demo_v1.yaml

# 3. Lint
make lint

# 4. Run witness
make run-witness CAP=test.e2e_demo_v1 WIT=e2e_check

# 5. Create test fixture
echo '{"test": true}' > artifacts/examples/test_pass.json

# 6. Add to test suite
# Edit tests/test_demo_witnesses.py

# 7. Run test
pytest tests/test_demo_witnesses.py::test_e2e_demo -v

# 8. Generate digest
make digest

# 9. Sign
make sign SIGNING_KEY=keys/dev_ed25519_sk.pem

# 10. Export KG
make kg

# 11. Compose in bundle
# Add to bundle, then:
make compose-bundle PROFILE=conversational BUNDLE=test_bundle

# 12. Generate SPA
make spa
```

**Checklist:**
- [ ] Each step succeeds
- [ ] No errors in pipeline
- [ ] All outputs generated
- [ ] End-to-end flow works

---

## 15. Pre-Release Checklist

### 15.1 Code Quality

```bash
# Run linters
make lint
make lint-strict

# Run tests
make test

# Check for TODOs
grep -r "TODO" capsules/ bundles/ profiles/ scripts/
```

- [ ] All capsules lint cleanly
- [ ] All bundles lint cleanly
- [ ] All tests pass
- [ ] No critical TODOs remaining
- [ ] Code reviewed

### 15.2 Documentation

- [ ] README.md updated with new features
- [ ] MIGRATION_GUIDE.md accurate
- [ ] TEST_WORKFLOWS.md (this doc) updated
- [ ] All example commands tested
- [ ] Changelog updated
- [ ] API docs current (if applicable)

### 15.3 Security

```bash
# Check for hardcoded secrets
grep -rE "(api_key|password|secret|token)" --include="*.yaml" --include="*.py" capsules/ scripts/

# Check permissions on key files
ls -la keys/

# Verify keys not in git
git ls-files keys/
```

- [ ] No hardcoded secrets
- [ ] Private keys have 600 permissions
- [ ] Keys not tracked in git
- [ ] .gitignore comprehensive
- [ ] Sandbox isolation verified

### 15.4 Artifacts

```bash
# Clean and rebuild
make clean
make smoke
make spa
```

- [ ] Clean build succeeds
- [ ] All artifacts regenerate cleanly
- [ ] SPA builds without errors
- [ ] No stale files in artifacts/

### 15.5 Dependencies

```bash
# Check requirements
cat requirements.txt

# Freeze current environment
make freeze

# Test with fresh venv
make clean-venv
make setup
make test
```

- [ ] requirements.txt up to date
- [ ] Fresh venv setup works
- [ ] All dependencies have versions
- [ ] No security vulnerabilities (`pip audit` if available)

### 15.6 Version & Tags

```bash
# Check version consistency
grep -r "version.*0.1" README.md capsules/ bundles/

# Tag release
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

- [ ] Version numbers consistent
- [ ] Git tag created
- [ ] Tag follows semver
- [ ] Tag pushed to remote

### 15.7 Demo Scenarios

Test both demo scenarios:

```bash
# GREEN demo (should pass)
make demo-cite-green

# RED demo (should fail but exit 0 due to ALLOW_RED)
make demo-cite-red

# Verify receipts
ls -lt artifacts/out/witness_*.signed.json | head -2
```

- [ ] GREEN demo passes
- [ ] RED demo fails as expected
- [ ] Signed receipts created
- [ ] Signatures verify

### 15.8 CI/CD

If using CI/CD:

```bash
# Check workflow files
ls -la .github/workflows/

# Validate workflow syntax (if using act)
act -l

# Run workflows locally
act push
```

- [ ] All workflow files present
- [ ] Workflows pass locally
- [ ] No secrets exposed in workflows
- [ ] Artifact uploads work

### 15.9 Performance

```bash
# Time operations
time make lint
time make digest
time make kg
time make spa
```

- [ ] Lint completes in reasonable time (< 5s typical)
- [ ] Digest generation fast (< 10s)
- [ ] KG export completes (< 30s)
- [ ] SPA generation fast (< 15s)

### 15.10 Browser Compatibility

Test SPA in multiple browsers:

- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari (if macOS)
- [ ] Edge
- [ ] Mobile browsers (iOS Safari, Chrome Mobile)

### 15.11 Final Checks

- [ ] All new capsules have tests
- [ ] All new capsules signed
- [ ] All bundles reference valid capsules
- [ ] All profiles work with bundles
- [ ] All LLM templates render correctly
- [ ] Migration guide tested
- [ ] Docker image builds
- [ ] Sandbox smoke tests pass
- [ ] Knowledge graph exports cleanly
- [ ] SPA works offline
- [ ] Examples in README work
- [ ] No broken links in docs
- [ ] License file present
- [ ] Contributing guide present (if open source)

---

## Quick Command Reference

```bash
# Setup
make setup
make keygen-dev

# Minting
make scaffold DOMAIN=x NAME=y TITLE="z" STATEMENT="w" WITNESS=check
make mint-profile PROFILE_NAME=p PROFILE_TITLE="t"

# Validation
make lint
make lint-strict
make lint-schema SCHEMA=schemas/capsule.schema.v1.json
make test

# Witnesses
make run-witness CAP=x WIT=y
make witness-sandbox CAPSULE=x WITNESS=y JSON=1 ENV_VARS="-e K=V"

# Digests & Signing
make digest
make sign SIGNING_KEY=keys/dev_ed25519_sk.pem
make verify PUBLIC_KEY=keys/dev_ed25519_pk.pem

# Composition
make compose
make compose-bundle PROFILE=p BUNDLE=b

# Export
make kg
make spa

# Migration
make migrate TARGET=path FROM_VERSION=v1 TO_VERSION=v2 DRY_RUN=1

# Full Pipeline
make smoke
```

---

## Troubleshooting

### Common Issues

**Issue: Lint errors for new capsules**
```bash
# Check specific capsule
python scripts/capsule_linter.py capsules/domain/name_v1.yaml

# Common fixes:
# - Ensure required fields present
# - Check YAML syntax
# - Verify witness code section
```

**Issue: Witness fails in sandbox**
```bash
# Debug by running locally first
make run-witness CAP=x WIT=y RUNENV="DEBUG=1"

# Check sandbox logs
docker logs <container_id>
```

**Issue: Signature verification fails**
```bash
# Check key mismatch
openssl pkey -in keys/dev_ed25519_sk.pem -pubout

# Regenerate keys if needed
make keygen-dev
```

**Issue: KG export fails**
```bash
# Validate TTL syntax
rapper -i turtle artifacts/out/capsules.ttl

# Check SHACL constraints
pyshacl -s shacl/truthcapsule.shacl.ttl artifacts/out/capsules.ttl
```

**Issue: SPA doesn't load**
```bash
# Check browser console (F12)
# Common issues:
# - CORS policy (use file:// or serve with http-server)
# - Missing dependencies (rebuild with make spa-offline)
# - JavaScript errors (check syntax)
```

---

## Notes

- Always test in a clean environment before release
- Keep test fixtures minimal but realistic
- Document any manual verification steps
- Update this checklist as new features are added
- Use dry-run mode for destructive operations
- Maintain backups of production data

**Last Updated:** 2025-01-11
**Version:** 1.0.0
