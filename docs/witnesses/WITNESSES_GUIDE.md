# Witnesses Guide - Execution & Security

**Version:** 1.0
**Date:** 2025-11-07
**Purpose:** Comprehensive guide to executing and securing truth capsule witnesses

---

## Overview

**Witnesses** are executable code artifacts embedded in truth capsules that verify adherence to rules, validate structure, or check compliance. They enable:

- **Automated verification**: Check outputs against capsule requirements
- **CI integration**: Gate merges on compliance
- **Self-documenting rules**: Code IS the specification
- **Deterministic validation**: Same code, same result

**⚠️ CRITICAL**: Witnesses execute arbitrary code. **YOU** are responsible for safe execution.

---

## Table of Contents

1. [Execution Model](#execution-model)
2. [Security & Sandboxing](#security--sandboxing)
3. [Language Support](#language-support)
4. [Running Witnesses](#running-witnesses)
5. [Writing Witnesses](#writing-witnesses)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)
8. [Examples](#examples)

---

## Execution Model

### Witness Lifecycle

```
1. Load Capsule (YAML)
   ↓
2. Parse witness definition (name, language, code, env, etc.)
   ↓
3. Prepare execution environment (workdir, env vars, timeout)
   ↓
4. Execute code in sandbox
   ↓
5. Capture stdout, stderr, exit code
   ↓
6. Determine result: PASS (exit 0) | FAIL (exit ≠0) | TIMEOUT
```

### Exit Code Semantics

| Exit Code | Meaning | Example |
|-----------|---------|---------|
| `0` | **PASS** - Witness succeeded | All assertions passed |
| `1` | **FAIL** - Witness failed | Assertion error, missing field |
| `2+` | **ERROR** - Execution error | Syntax error, file not found |
| `124` (convention) | **TIMEOUT** - Exceeded `timeout_ms` | Infinite loop, hanging process |

**Python note**: Use `assert` statements. Failed assertions raise `AssertionError` with exit code 1.

**Bash note**: Use `exit 1` for failures. Most commands return non-zero on error.

---

## Security & Sandboxing

### The Threat Model

Witnesses are **untrusted code**. Assume:
- Code may be malicious (backdoors, exfiltration)
- Code may be buggy (infinite loops, resource exhaustion)
- Code may try to escape sandbox (privilege escalation)

**Your responsibility**: Run witnesses in an isolated environment that limits damage.

### Recommended Sandboxing Strategies

#### Level 1: Process Isolation (Minimum)

**Python Example (using `subprocess` with limits):**

```python
import subprocess
import os

def run_witness(witness_config, capsule_file):
    """Run a witness with basic process isolation."""

    # Extract witness fields
    name = witness_config.get("name")
    language = witness_config.get("language")
    code = witness_config.get("code")
    env = witness_config.get("env", {})
    timeout_ms = witness_config.get("timeout_ms", 5000)
    entrypoint = witness_config.get("entrypoint", language)

    # Write code to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix=f'.{language}',
        delete=False
    ) as f:
        f.write(code)
        code_file = f.name

    try:
        # Prepare environment (explicit allowlist only)
        safe_env = {k: str(v) for k, v in env.items()}

        # Run with timeout
        result = subprocess.run(
            [entrypoint, code_file],
            capture_output=True,
            timeout=timeout_ms / 1000.0,  # Convert to seconds
            env=safe_env,
            cwd=os.getcwd()
        )

        return {
            "name": name,
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "returncode": result.returncode,
            "stdout": result.stdout.decode('utf-8', errors='replace'),
            "stderr": result.stderr.decode('utf-8', errors='replace')
        }

    except subprocess.TimeoutExpired:
        return {
            "name": name,
            "status": "TIMEOUT",
            "returncode": 124,
            "stdout": "",
            "stderr": f"Execution exceeded {timeout_ms}ms"
        }

    finally:
        os.unlink(code_file)
```

**Limitations**:
- No CPU/memory limits
- No filesystem restrictions
- No network restrictions
- Can access parent process environment

#### Level 2: Container Isolation (Recommended for Production)

**Docker Example:**

```bash
# Build a witness runner container
docker build -t witness-runner - <<'EOF'
FROM python:3.11-slim
RUN useradd -m -u 1000 witness
USER witness
WORKDIR /workspace
CMD ["python3"]
EOF

# Run witness in container
docker run \
  --rm \
  --network none \
  --memory 128m \
  --cpus 0.5 \
  --read-only \
  --tmpfs /tmp:rw,size=10m \
  --user 1000:1000 \
  -v /path/to/artifacts:/workspace:ro \
  -e PS_REPORT="/workspace/problem_solving_ok.json" \
  witness-runner \
  python3 -c "$(cat witness_code.py)"
```

**Advantages**:
- Network disabled (`--network none`)
- Memory limited (`--memory 128m`)
- CPU limited (`--cpus 0.5`)
- Filesystem read-only (`--read-only`)
- Non-root user (`--user 1000:1000`)
- Isolated process namespace

#### Level 3: VM Isolation (Maximum Security)

Use Firecracker, gVisor, or Kata Containers for hypervisor-level isolation.

**When to use**:
- Untrusted third-party capsules
- Regulatory requirements
- High-value targets (financial, healthcare)

---

## Language Support

### Python

**Default entrypoint**: `python3` (or `python`)

**Execution model**:
```python
# Code is executed as a script
exec(code, globals(), locals())
```

**Example witness:**
```yaml
witnesses:
  - name: check_fields
    language: python
    code: |-
      import json, os

      data = json.load(open(os.getenv("DATA_FILE")))
      assert "required_field" in data, "Missing required_field"
```

**Common patterns**:
- Use `assert` for validation
- Read files via `os.getenv()` for paths
- Print to stdout for debugging (captured)
- Raise exceptions for failures

### Node.js

**Default entrypoint**: `node`

**Example witness:**
```yaml
witnesses:
  - name: check_json_schema
    language: node
    code: |-
      const fs = require('fs');
      const path = process.env.DATA_FILE || 'data.json';
      const data = JSON.parse(fs.readFileSync(path, 'utf8'));

      if (!data.required_field) {
        console.error('Missing required_field');
        process.exit(1);
      }
```

**Common patterns**:
- Use `process.exit(1)` for failures
- Read `process.env` for configuration
- Use `console.error()` for failure messages

### Bash/Shell

**Default entrypoint**: `bash` or `sh`

**Example witness:**
```yaml
witnesses:
  - name: file_exists
    language: bash
    code: |-
      DATA_FILE="${DATA_FILE:-data.json}"

      if [[ ! -f "$DATA_FILE" ]]; then
        echo "File not found: $DATA_FILE" >&2
        exit 1
      fi

      # Check file is valid JSON
      jq empty "$DATA_FILE" || exit 1
```

**Common patterns**:
- Use `set -e` for fail-fast
- Use `exit 1` for failures
- Echo errors to stderr (`>&2`)
- Use `[[ ]]` for conditionals

---

## Running Witnesses

### Basic Usage

```bash
# Run all witnesses in capsules directory
python run_witnesses.py truth-capsules-v1/capsules

# Run witnesses for specific capsule
python run_witnesses.py truth-capsules-v1/capsules/pedagogy.problem_solving_v1.yaml

# JSON output for CI
python run_witnesses.py truth-capsules-v1/capsules --json
```

### Output Format

**Human-readable**:
```
Running witnesses for pedagogy.problem_solving_v1...
  ✓ five_step_gate PASS

Running witnesses for business.decision_log_v1...
  ✗ decision_log_gate FAIL
    Error: Missing field: decision
```

**JSON format** (`--json`):
```json
[
  {
    "capsule": "pedagogy.problem_solving_v1",
    "status": "GREEN",
    "witness_results": [
      {
        "name": "five_step_gate",
        "result": "GREEN",
        "returncode": 0,
        "stdout": "",
        "stderr": ""
      }
    ]
  },
  {
    "capsule": "business.decision_log_v1",
    "status": "RED",
    "witness_results": [
      {
        "name": "decision_log_gate",
        "result": "RED",
        "returncode": 1,
        "stdout": "",
        "stderr": "AssertionError: Missing field: decision"
      }
    ]
  }
]
```

### Exit Codes

| Exit Code | Meaning |
|-----------|---------|
| `0` | All witnesses passed |
| `1` | One or more witnesses failed |
| `2` | Invalid arguments or file not found |

---

## Writing Witnesses

### Design Principles

1. **One witness, one check**: Don't validate 10 things in one witness
2. **Clear failure messages**: Use descriptive assertions
3. **Explicit inputs**: Use `env:` to pass file paths, not hardcoded
4. **Fast execution**: Aim for <1 second per witness
5. **Deterministic**: Same input → same output (no random, no network)

### Example: Validating a Decision Log

**Capsule**: `business.decision_log_v1.yaml`

**Rule**: Decision records must include decision, ≥3 options, ≥2 criteria, and a rationale mentioning a trade-off.

**Witness**:
```yaml
witnesses:
  - name: decision_log_gate
    language: python
    env:
      DEC_REPORT: "artifacts/examples/decision_log_ok.json"
    timeout_ms: 2000
    code: |-
      import json, os

      # Read decision log from environment variable
      path = os.getenv("DEC_REPORT", "artifacts/examples/decision_log_ok.json")
      data = json.load(open(path))

      # Check required field
      assert data.get("decision"), "Missing field: decision"

      # Check options (must have ≥3)
      options = data.get("options", [])
      assert isinstance(options, list) and len(options) >= 3, \
        f"Need >= 3 options, found {len(options)}"

      # Check criteria (must have ≥2)
      criteria = data.get("criteria", [])
      assert isinstance(criteria, list) and len(criteria) >= 2, \
        f"Need >= 2 criteria, found {len(criteria)}"

      # Check rationale mentions trade-off
      rationale = data.get("rationale", "").lower()
      has_tradeoff = "trade-off" in rationale or "because" in rationale
      assert has_tradeoff, "Rationale must mention trade-off or reasoning"
```

**Test data** (`artifacts/examples/decision_log_ok.json`):
```json
{
  "decision": "Use PostgreSQL for primary database",
  "options": ["PostgreSQL", "MySQL", "MongoDB", "SQLite"],
  "criteria": ["Performance", "Scalability", "Team expertise"],
  "rationale": "PostgreSQL chosen because of strong ACID guarantees and team expertise, trade-off is higher operational complexity vs NoSQL"
}
```

**Usage**:
```bash
# Set environment and run
DEC_REPORT=my_decision.json python run_witnesses.py capsules/business.decision_log_v1.yaml
```

### Example: Checking Rollback Plan

**Capsule**: `ops.rollback_plan_v1.yaml`

**Rule**: Deploy plans must include rollback step with trigger conditions and owner.

**Witness**:
```yaml
witnesses:
  - name: rollback_present
    language: python
    env:
      OPS_PLAN: "artifacts/examples/ops_plan_ok.json"
    code: |-
      import json, os

      path = os.getenv("OPS_PLAN", "artifacts/examples/ops_plan_ok.json")
      data = json.load(open(path))

      # Check rollback section exists
      rollback = data.get("rollback", {})

      # Validate rollback has required fields
      assert rollback.get("steps"), "Rollback missing 'steps'"
      assert rollback.get("trigger"), "Rollback missing 'trigger' conditions"
      assert rollback.get("owner"), "Rollback missing 'owner'"
```

---

## Best Practices

### 1. Use Environment Variables for Inputs

**❌ Bad**: Hardcoded paths
```python
data = json.load(open("/absolute/path/to/file.json"))
```

**✅ Good**: Environment variables with defaults
```python
path = os.getenv("DATA_FILE", "artifacts/examples/default.json")
data = json.load(open(path))
```

### 2. Provide Clear Error Messages

**❌ Bad**: Vague assertion
```python
assert data["key"]
```

**✅ Good**: Descriptive message
```python
assert data.get("key"), "Missing required field 'key' in data"
```

### 3. Set Appropriate Timeouts

**❌ Bad**: No timeout (default 5000ms may be too short/long)
```yaml
witnesses:
  - name: heavy_check
    language: python
    code: ...
```

**✅ Good**: Explicit timeout based on complexity
```yaml
witnesses:
  - name: heavy_check
    language: python
    timeout_ms: 30000  # 30 seconds for complex validation
    code: ...
```

### 4. Keep Witnesses Focused

**❌ Bad**: One witness validates everything
```python
# Check fields, schemas, business logic, permissions...
assert data.get("field1")
assert data.get("field2")
# ... 50 more lines
```

**✅ Good**: Multiple focused witnesses
```yaml
witnesses:
  - name: required_fields
    language: python
    code: |-
      assert data.get("field1") and data.get("field2")

  - name: schema_valid
    language: python
    code: |-
      import jsonschema
      jsonschema.validate(data, schema)

  - name: business_rules
    language: python
    code: |-
      assert data["amount"] > 0
```

### 5. Make Witnesses Deterministic

**❌ Bad**: Depends on current time or random
```python
import time
assert data["timestamp"] > time.time() - 3600  # Fails after 1 hour
```

**✅ Good**: Validate structure, not time-dependent values
```python
assert "timestamp" in data
assert isinstance(data["timestamp"], (int, float))
```

### 6. Document Witness Purpose

**❌ Bad**: Generic name
```yaml
witnesses:
  - name: check1
    language: python
```

**✅ Good**: Descriptive name
```yaml
witnesses:
  - name: rollback_plan_complete
    language: python
```

---

## Troubleshooting

### Witness Fails Locally But Passes in CI

**Cause**: Environment differences (file paths, environment variables)

**Solution**:
- Use relative paths or environment variables
- Check `env:` configuration in witness
- Verify working directory with `workdir:` field

### Witness Times Out

**Cause**: Infinite loop, network call, large file processing

**Solutions**:
- Increase `timeout_ms` if legitimately slow
- Remove network calls (use local files)
- Optimize code (use streaming for large files)
- Add debug prints to find hang point

### Witness Passes Incorrectly (False Positive)

**Cause**: Weak validation logic

**Solutions**:
- Add more assertions
- Check for both presence AND validity
- Use schema validation libraries
- Test with known-bad inputs

### Witness Fails Incorrectly (False Negative)

**Cause**: Too strict validation

**Solutions**:
- Review assertion logic
- Check for edge cases (empty lists, null values)
- Make assertions more permissive (e.g., `len(x) >= 1` not `len(x) == 3`)

### Import Errors in Python Witnesses

**Cause**: Missing dependencies in sandbox

**Solutions**:
- Use stdlib only (json, os, re, etc.)
- Install dependencies in sandbox container
- Vendor small libraries into witness code

---

## Examples

### Example 1: JSON Schema Validation (Python)

```yaml
witnesses:
  - name: schema_valid
    language: python
    env:
      DATA_FILE: "output.json"
      SCHEMA_FILE: "schemas/output_schema.json"
    code: |-
      import json
      import os

      # Note: jsonschema not in stdlib, needs to be installed in sandbox
      try:
          import jsonschema
      except ImportError:
          print("Warning: jsonschema not available, skipping validation")
          exit(0)  # Or exit(1) to fail if schema validation is required

      data = json.load(open(os.getenv("DATA_FILE")))
      schema = json.load(open(os.getenv("SCHEMA_FILE")))

      jsonschema.validate(data, schema)
```

### Example 2: Regex Pattern Matching (Bash)

```yaml
witnesses:
  - name: no_secrets_in_logs
    language: bash
    env:
      LOG_FILE: "application.log"
    code: |-
      set -e

      LOG_FILE="${LOG_FILE:-application.log}"

      # Check for common secret patterns
      if grep -qE '(api[_-]?key|secret|password|token)\s*[:=]' "$LOG_FILE"; then
        echo "ERROR: Potential secrets found in log file" >&2
        exit 1
      fi

      echo "No secrets detected in logs"
```

### Example 3: File Structure Check (Node)

```yaml
witnesses:
  - name: package_json_valid
    language: node
    env:
      PKG_FILE: "package.json"
    code: |-
      const fs = require('fs');
      const path = process.env.PKG_FILE || 'package.json';

      const pkg = JSON.parse(fs.readFileSync(path, 'utf8'));

      // Check required fields
      const required = ['name', 'version', 'description'];
      for (const field of required) {
        if (!pkg[field]) {
          console.error(`Missing required field: ${field}`);
          process.exit(1);
        }
      }

      // Check version format
      if (!/^\d+\.\d+\.\d+/.test(pkg.version)) {
        console.error(`Invalid version format: ${pkg.version}`);
        process.exit(1);
      }

      console.log('package.json is valid');
```

### Example 4: Multi-Witness Capsule

```yaml
id: code.python_quality_v1
version: 1.0.0
domain: code
statement: "Python code must pass linting, type checking, and have >= 80% test coverage"

witnesses:
  - name: pylint_check
    language: bash
    timeout_ms: 10000
    code: |-
      set -e
      pylint --fail-under=8.0 src/

  - name: mypy_check
    language: bash
    timeout_ms: 10000
    code: |-
      set -e
      mypy src/

  - name: coverage_check
    language: python
    timeout_ms: 5000
    code: |-
      import json

      # Read coverage report
      coverage = json.load(open("coverage.json"))
      total_coverage = coverage["totals"]["percent_covered"]

      assert total_coverage >= 80.0, \
        f"Coverage {total_coverage}% below 80% threshold"
```

---

## CI Integration

### GitHub Actions Example

```yaml
name: Validate Capsule Witnesses

on: [push, pull_request]

jobs:
  witness-check:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pyyaml

      - name: Run witnesses
        run: |
          python run_witnesses.py truth-capsules-v1/capsules --json > results.json

      - name: Check results
        run: |
          if jq -e '.[] | select(.status == "RED")' results.json; then
            echo "One or more witnesses failed"
            exit 1
          fi

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: witness-results
          path: results.json
```

---

## Advanced Topics

### Witness Composition

Create witnesses that compose with others:

```yaml
# Base capsule
id: data.schema_v1
witnesses:
  - name: schema_check
    language: python
    code: |-
      # Validate JSON schema
      ...

# Extending capsule
id: data.business_rules_v1
dependencies:
  - data.schema_v1  # Assumes schema validation runs first
witnesses:
  - name: business_rules_check
    language: python
    code: |-
      # Assume schema is valid, check business logic
      ...
```

### Witness Caching

For expensive witnesses, cache results:

```python
import hashlib
import json
import os

cache_dir = ".witness_cache"
os.makedirs(cache_dir, exist_ok=True)

# Compute content hash
data_file = os.getenv("DATA_FILE")
with open(data_file, "rb") as f:
    content_hash = hashlib.sha256(f.read()).hexdigest()

cache_file = f"{cache_dir}/{content_hash}.json"

# Check cache
if os.path.exists(cache_file):
    cached_result = json.load(open(cache_file))
    if cached_result["status"] == "PASS":
        print(f"Cache hit: {cache_file}")
        exit(0)

# Run validation...
# ...

# Cache result
json.dump({"status": "PASS"}, open(cache_file, "w"))
```

---

## Security Checklist

Before running witnesses in production:

- [ ] **Parse YAML safely** (`yaml.safe_load`, not `yaml.load`)
- [ ] **Sandbox execution** (containers, VMs, or process isolation)
- [ ] **Enforce timeouts** (prevent infinite loops)
- [ ] **Limit resources** (CPU, memory, disk, network)
- [ ] **Read-only filesystem** (except `/tmp`)
- [ ] **Explicit environment** (allowlist only)
- [ ] **Drop privileges** (non-root user)
- [ ] **Capture outputs** (stdout, stderr, exit code)
- [ ] **Audit witness code** (review before running)
- [ ] **Isolate network** (no external calls)

---

## References

- **CAPSULE_SCHEMA_v1.md**: Complete witness field reference
- **LINTER_GUIDE.md**: Validating witness structure
- **CI_GUIDE.md**: Running witnesses in CI pipelines
- **QUICKSTART.md**: Basic witness examples

---

*Version: 1.0*
*Last Updated: 2025-11-07*
*Next Review: Based on community feedback*

---

**Witnesses enable Truth Capsules to be self-validating. Use them wisely.**
