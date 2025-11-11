# CHEATSHEET

Quick reference for linting, composing, testing, exporting, and graph-loading **Truth Capsules**.

> TL;DR: **lint → compose → (optional) sign → run witnesses → export KG → (optional) load Neo4j.**

---

## 0) Setup

```bash
# From repo root
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Common paths:

* Capsules: `capsules/*.yaml`
* Bundles: `bundles/*.yaml`
* Profiles: `profiles/*.yaml`
* Artifacts: `artifacts/out/` (exports land here)

Ensure writable artifacts dir:

```bash
mkdir -p artifacts/out
chmod -R u+rwX,go+rX artifacts/out
```

---

## 1) Lint & Validate

```bash
# Lint all capsules (schema + provenance checks)
python scripts/capsule_linter.py capsules

# Strict mode (requires review.status=approved, etc.)
python scripts/capsule_linter.py capsules --strict --json
```

---

## 1.5) Digest Management

Capsules use SHA256 digests for integrity verification. The digest is calculated from core fields (id, version, domain, title, statement, assumptions, pedagogy).

```bash
# Verify all digests are correct
make digest-verify
# or
python scripts/capsule_digest.py capsules --verify

# Update/reset all digests (if capsule content changed)
make digest
# or
make digest-reset
# or
python scripts/capsule_digest.py capsules

# Get JSON output for CI/automation
python scripts/capsule_digest.py capsules --verify --json
```

**When to update digests:**
- After editing capsule content (title, statement, assumptions, pedagogy)
- Before signing capsules (digest must be current)
- When migrating from old digest calculation method

**Note:** Digests are stored in `provenance.signing.digest` and should be updated before creating signatures.

---

## 2) Discover Profiles & Bundles

```bash
# List profiles (with aliases)
python scripts/compose_capsules_cli.py --root . --list-profiles

# List bundles
python scripts/compose_capsules_cli.py --root . --list-bundles
```

Profiles you can use:

```
Available Profiles:

  profile.ci.gates_v1
    Title: CI Quality Gates — Fail Fast

  profile.dev.code_assistant_v1
    Title: Developer Velocity — Code Assistant & Review Copilot

  profile.macgyver_v1
    Title: MacGyver Upgrade (Conversational)

  profile.support_public_agent_v1
    Title: Customer Support Copilot (Public-Facing)
```
---

## 3) Compose System Prompts

> **Important:** `--capsule` expects **IDs**, not file paths.
> Example ID: `llm.citation_required_v1`

```bash
# Single capsule
python scripts/compose_capsules_cli.py \
  --root . \
  --profile conversational \
  --capsule llm.citation_required_v1 \
  --out demos/cite/prompt.txt \
  --manifest demos/cite/manifest.json

# From a bundle
python scripts/compose_capsules_cli.py \
  --root . \
  --profile conversational \
  --bundle conversation_red_team_baseline_v1 \
  --out demos/conv_redteam/prompt.txt \
  --manifest demos/conv_redteam/manifest.json

# Combine bundles + extra capsules
python scripts/compose_capsules_cli.py \
  --root . \
  --profile pedagogical \
  --bundle conversation_pedagogy_v1 \
  --capsule llm.steelmanning_v1 \
  --out demos/pedagogy/prompt.txt
```

---

## 4) Run Witnesses (Executable Checks)

```bash
python scripts/run_witnesses.py capsules [--json]
```

---

## 5) Sign / Verify (optional)

**Important:** Always update digests before signing!

```bash
# 1. Update digests first
make digest

# 2. Sign with Ed25519
python scripts/capsule_sign.py capsules --key $SIGNING_KEY
# or
make sign SIGNING_KEY=keys/my_key.pem

# 3. Verify signatures
python scripts/capsule_verify.py capsules --pubkey $PUBLIC_KEY
# or
make verify
```

**Workflow:**
1. Edit capsule → update digest → sign → commit
2. Never sign without updating digest first (signature will be invalid)

---

## 6) Export to Knowledge Graph

```bash
python scripts/export_kg.py
# Outputs:
#   artifacts/out/capsules.ttl     (RDF/Turtle)
#   artifacts/out/capsules.ndjson  (NDJSON-LD for property graphs)
```

---

## 7) Neo4j Quick-Load (two options)

### A) Neo4j 4.4 + APOC (extended) + `apoc.load.json` (NDJSON)

> Requires 4.4 with **apoc-all** matching 4.4 (e.g. `apoc-4.4.0.39-all.jar`) and `dbms.security.procedures.unrestricted=apoc.*`

```bash
# Start a 4.4 container (mount plugins & imports)
docker rm -f neo4j44 2>/dev/null || true
docker run -d --name neo4j44 \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e dbms.security.procedures.unrestricted=apoc.* \
  -e apoc.import.file.enabled=true \
  -v "$PWD/.neo4j44/plugins":/plugins:ro \
  -v "$PWD/artifacts/out":/import/artifacts/out:ro \
  neo4j:4.4

# Wait for Bolt (simple ping)
until docker exec neo4j44 cypher-shell -u neo4j -p password --encryption=false "RETURN 1" >/dev/null 2>&1; do sleep 1; done

# Check apoc
docker exec neo4j44 cypher-shell -u neo4j -p password --encryption=false \
  "RETURN apoc.version() AS apoc_version;"

# Create constraints (must be separate commands)
docker exec neo4j44 cypher-shell -u neo4j -p password --encryption=false \
  "CREATE CONSTRAINT capsule_pk IF NOT EXISTS FOR (c:Capsule) REQUIRE c.iri IS UNIQUE;"
docker exec neo4j44 cypher-shell -u neo4j -p password --encryption=false \
  "CREATE CONSTRAINT witness_pk IF NOT EXISTS FOR (w:Witness) REQUIRE w.iri IS UNIQUE;"

# Load NDJSON (simplified, working version)
docker exec neo4j44 cypher-shell -u neo4j -p password --encryption=false "
WITH 'file:///artifacts/out/capsules.ndjson' AS URL
CALL apoc.load.json(URL) YIELD value AS v0
WITH v0,
     toString(coalesce(v0['@id'],'')) AS iri,
     toString(coalesce(v0.identifier, v0['@id'])) AS identifier,
     toString(coalesce(v0.title,'')) AS title,
     toString(coalesce(v0.statement,'')) AS statement,
     toString(coalesce(v0.domain,'')) AS domain,
     toString(coalesce(v0.version,'')) AS version,
     coalesce(v0.assumption, []) AS assumptions,
     coalesce(v0.hasWitness, []) AS witnesses
MERGE (c:Capsule {iri: iri})
  SET c.identifier  = identifier,
      c.title       = title,
      c.statement   = statement,
      c.domain      = domain,
      c.version     = version,
      c.assumptions = [x IN assumptions WHERE x IS NOT NULL AND x <> '' | toString(x)]
WITH c, witnesses
UNWIND CASE WHEN size(witnesses) = 0 THEN [null] ELSE witnesses END AS w
WITH c, w WHERE w IS NOT NULL
MERGE (wNode:Witness {iri: toString(w['@id'])})
  SET wNode.language = toString(coalesce(w.language,'')),
      wNode.codeHash = toString(coalesce(w.codeHash,'')),
      wNode.codeRef  = toString(coalesce(w.codeRef,''))
MERGE (c)-[:HAS_WITNESS]->(wNode);
"

# Sanity
docker exec neo4j44 cypher-shell -u neo4j -p password --encryption=false \
  "MATCH (c:Capsule) RETURN count(c) AS capsules;"
```

### B) Neo4j 5.x + n10s (RDF/Turtle import; **no APOC needed**)

```bash
# Start 5.x with n10s plugin (or use the built-in plugin manager)
docker rm -f neo4j5 2>/dev/null || true
docker run -d --name neo4j5 \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS='["n10s"]' \
  -v "$PWD/artifacts/out":/var/lib/neo4j/import/artifacts/out:ro \
  neo4j:5.20

until docker exec neo4j5 cypher-shell -u neo4j -p password "RETURN 1" >/dev/null 2>&1; do sleep 1; done

# Init n10s and import TTL
docker exec neo4j5 cypher-shell -u neo4j -p password \
  "CREATE CONSTRAINT capsule_pk IF NOT EXISTS FOR (c:Capsule) REQUIRE c.iri IS UNIQUE;"
docker exec neo4j5 cypher-shell -u neo4j -p password \
  "CALL n10s.graphconfig.init();"
docker exec neo4j5 cypher-shell -u neo4j -p password \
  'CALL n10s.rdf.import.fetch("file:///artifacts/out/capsules.ttl","Turtle") YIELD triplesLoaded RETURN triplesLoaded;'
```

---

## 8) Handy “Wow” Cypher Queries

```cypher
// Coverage by domain
MATCH (c:Capsule) RETURN c.domain AS domain, count(*) AS n ORDER BY n DESC;

// Capsules missing title/statement (hygiene check)
MATCH (c:Capsule) WHERE coalesce(c.title,'')='' OR coalesce(c.statement,'')=''
RETURN c.iri, c.title, c.statement;

// Assumptions fan-out (top 10)
MATCH (c:Capsule) UNWIND coalesce(c.assumptions,[]) AS a
WITH a, count(*) AS n ORDER BY n DESC LIMIT 10
RETURN a AS assumption, n;

// Witness presence
MATCH (c:Capsule) OPTIONAL MATCH (c)-[:HAS_WITNESS]->(w:Witness)
RETURN c.domain, count(w) AS witnesses, count(*) AS capsules
ORDER BY witnesses DESC;

// Find unsafe strings (e.g., TODO)
MATCH (c:Capsule)
WHERE c.statement CONTAINS 'TODO' OR c.title CONTAINS 'TODO'
RETURN c.iri, c.title;
```

---

## 9) Minimal Capsule Template

```yaml
id: llm.example_cap_v1
version: 1.0.0
domain: llm
title: Short title
statement: One-line policy or rule the model must satisfy.
assumptions:
  - Assumptions are explicit, testable statements.
pedagogy:
  - kind: Socratic
    text: What evidence would falsify this?
  - kind: Aphorism
    text: Absence of evidence is not evidence of absence.
hasWitness:
  - id: witness.llm.example_cap_v1.py
    language: python
    codeRef: scripts/witnesses/example.py
    codeHash: <sha256>
```

---

## 10) Quick Demos (compose → use)

```bash
# Red-team conversational demo
python scripts/compose_capsules_cli.py \
  --root . \
  --profile conversational \
  --bundle conversation_red_team_baseline_v1 \
  --out demos/redteam/prompt.txt

# Code review mini-bundle
python scripts/compose_capsules_cli.py \
  --root . \
  --profile code_patch \
  --bundle pr_review_minibundle_v1 \
  --out demos/pr/prompt.txt
```

---

## 11) Troubleshooting

* **"No capsules selected"**: `--capsule` needs **IDs**, not file paths.
* **Permission denied to artifacts/out**: `chmod -R u+rwX,go+rX artifacts/out`
* **APOC not found**: Version mismatch or missing jar; check `RETURN apoc.version()`.
* **`apoc.meta.*` sandboxed**: avoid `apoc.meta.type` unless unrestricted; use pure Cypher typing guards.
* **"Expected exactly one statement" constraint error**: Split multi-statement queries into separate `cypher-shell` calls.
* **"IS STRING/IS LIST/IS MAP" type errors**: Cypher doesn't support these operators; use `size()`, `IS NULL`, and filtering instead.
* **"Collections containing collections"**: don't set nested lists as properties; flatten to strings.
* **Bolt connection refused**: wait loop until `RETURN 1` succeeds before running queries.
* **File URL errors**: confirm path is visible inside container (`/import/...` or `/var/lib/neo4j/import/...`), and plugin's `*_import_file_enabled=true` if using APOC.

---

## 12) Using the `llm` CLI with Truth Capsules

> Works great for quick, repeatable runs that honor your composed **system prompts**.

### Install & keys

```bash
# Recommended: install via pipx
pipx install llm

# (Optional) add providers/plugins you use
# Examples (install only what you need):
llm install llm-openai
llm install llm-claude
llm install llm-ollama   # local models via Ollama

# Set API keys (or use env vars)
llm keys set openai
llm keys set anthropic
```

### Core one-liners (compose → run)

```bash
# 1) Compose (example)
python scripts/compose_capsules_cli.py \
  --root . \
  --profile conversational \
  --bundle conversation_red_team_baseline_v1 \
  --out demos/redteam/prompt.txt \
  --manifest demos/redteam/manifest.json

# 2) Run a single prompt with the composed system prompt
SYS="$(cat demos/redteam/prompt.txt)"
llm -m openai:gpt-4o-mini --system "$SYS" \
  "You are my assistant. Red-team this product pitch in 8 bullets."
```

```bash
# Pipe long inputs (code, diffs, transcripts) and still inject the system
SYS="$(cat demos/redteam/prompt.txt)"
git show --stat --patch | llm -m openai:gpt-4o-mini --system "$SYS" \
  "Review the diff using the capsule rules."
```

```bash
# Save a quick shell helper so you never forget the --system step
llm_with_capsules () { local sys="$1"; shift; llm --system "$(cat "$sys")" "$@"; }

# Example usage:
llm_with_capsules demos/redteam/prompt.txt -m openai:gpt-4o-mini \
  "Sanity-check this deployment plan with the rollback capsule assumptions."
```

### Structured / JSON outputs

Use model options to push structured output (varies by model/provider). Example for OpenAI JSON responses:

```bash
SYS="$(cat demos/toolrunner/prompt.txt)"  # e.g., built from tool_runner profile
llm -m openai:gpt-4o-mini --system "$SYS" \
  -o response_format=json \
  'Given this schema, return a valid JSON object that passes the contract.'
```

### Conversations you can resume

You can keep the same **system** and iterate by re-using your shell function or re-calling with the same system file. (If you prefer named “sessions”, you can adopt your own wrapper that stores session prompts and re-applies `--system` on each call.)

---

## 13) Micro Demos with `llm`

### A) “PR Review Mini-bundle” (diff-first, tests, risk tags)

```bash
# Compose PR review mini-bundle
python scripts/compose_capsules_cli.py \
  --root . \
  --profile code_patch \
  --bundle pr_review_minibundle_v1 \
  --out demos/pr/prompt.txt

# Review current branch changes
SYS="$(cat demos/pr/prompt.txt)"
git diff main...HEAD | llm -m openai:gpt-4o-mini --system "$SYS" \
  "Perform capsule-compliant PR review. Highlight risky changes and propose tests."
```

### B) “Red-Team a Requirements Doc” (fast hygiene + reasoning)

```bash
python scripts/compose_capsules_cli.py \
  --root . \
  --profile conversational \
  --bundle conversation_red_team_baseline_v1 \
  --out demos/redteam/prompt.txt

SYS="$(cat demos/redteam/prompt.txt)"
cat docs/spec.md | llm -m anthropic:claude-3-5-sonnet --system "$SYS" \
  "Identify assumptions to test, missing citations, and critical failure modes."
```

### C) **YouTube Transcript → Aphorisms → New Capsules**

> Rapidly mint new capsules from longform content.

```bash
# 1) Get a transcript (auto-captions acceptable for demo)
yt-dlp --write-auto-sub --sub-lang en --skip-download -o 'transcript.%(ext)s' \
  'https://www.youtube.com/watch?v=VIDEO_ID'
sed -n 's/<[^>]*>//g; s/^[0-9:.,-> ]\+//; /^[[:space:]]*$/d; p' transcript.en.vtt > demos/youtube/transcript.txt

# 2) Compose a pedagogy-forward system prompt
python scripts/compose_capsules_cli.py \
  --root . \
  --profile pedagogical \
  --bundle conversation_pedagogy_v1 \
  --capsule llm.steelmanning_v1 \
  --out demos/youtube/pedagogy.txt

# 3) Extract aphorisms + Socratic Qs with `llm`
SYS="$(cat demos/youtube/pedagogy.txt)"
llm -m openai:gpt-4o-mini --system "$SYS" \
  "From this transcript, extract: 
   (1) 10 aphorisms (short, punchy, generalizable),
   (2) 10 Socratic questions (that teach the core ideas).
   Output as YAML with keys aphorisms:[], socratic:[]" \
   < demos/youtube/transcript.txt \
   > demos/youtube/extracted.yaml

# 4) Mint new capsules skeletons from extracted.yaml
python scripts/generate_action.py \
  --input demos/youtube/extracted.yaml \
  --template prompts/capsule_minter.txt \
  --out-dir capsules/generated

# 5) Lint and list
python scripts/capsule_linter.py capsules/generated
ls -1 capsules/generated/*.yaml
```

*(The `generate_action.py` step can be replaced by a small helper that reads `extracted.yaml` and writes capsule YAML using your capsule schema — whichever flow you prefer.)*

### D) Tool-Runner JSON contract quick-test

```bash
# Compose a tool-runner profile (JSON contract enforcer)
python scripts/compose_capsules_cli.py \
  --root . \
  --profile tool_runner \
  --bundle assistant_baseline_v1 \
  --capsule llm.tool_json_contract_v1 \
  --out demos/tools/prompt.txt

SYS="$(cat demos/tools/prompt.txt)"
SCHEMA="$(cat schemas/report.schema.v1.json)"
llm -m openai:gpt-4o-mini --system "$SYS" \
  "Using this JSON schema, produce a valid report object for the following input:
   <paste your input>
   SCHEMA:
   $SCHEMA" \
  -o response_format=json
```

---

## 14) Tips & Patterns

* **Always inject the composed system** (`--system "$(cat prompt.txt)"`). That’s the entire *point* of Truth Capsules: deterministic, curated behavior.
* Keep **model options** alongside runs:

  * Low-risk “CI-style”: `-o temperature=0.0`
  * Balanced: `-o temperature=0.2`
* For **repeatability**, check in your `manifest.json` next to the generated `prompt.txt`.
* Save a couple of **shell helpers** (`llm_with_capsules`, `pr_review`, etc.) to remove friction.
* When creating demos, prefer **stdin pipes** for long inputs:

  ```bash
  llm --system "$SYS" "Task here" < big_input.txt
  ```

---

## 15) Copy a ready-to-run `llm` command from the SPA

The Truth Capsule Composer SPA includes a **"Copy LLM Cmd"** feature that generates fully runnable bash commands with your composed system prompt auto-injected.

### How it works

1. **Compose a prompt** in the SPA (select profile, bundles, and/or capsules)
2. Click **💻 Copy LLM Cmd** in the header
3. **Pick a template** (OpenAI, Anthropic, Ollama, etc.)
4. **(Optional)** Type your user input or specify a file path
5. Click **📋 Copy Command**, then paste in your terminal

### What you get

The SPA generates a bash command with:
- **System prompt** via literal heredoc (`read -r -d '' TC_SYSTEM <<'__TC_SYSTEM__'`)
- **User input** safely quoted (POSIX single-quote escaping)
- **Model flags** from the template (e.g., `--no-stream` for Anthropic)
- **Live preview** updates as you type, so you see exactly what will be copied

### Example output (OpenAI / arg mode)

```bash
read -r -d '' TC_SYSTEM <<'__TC_SYSTEM__'
SYSTEM: Profile=Conversational Guidance
POLICY: Cite or abstain; follow Plan→Verify→Answer; ask ONE crisp follow-up if required.
...
__TC_SYSTEM__
llm -m gpt-4o-mini --system "$TC_SYSTEM" <<< 'Perform capsule-compliant PR review. Highlight risky changes and propose tests.'
```

### Example output (Anthropic / stdin mode)

```bash
read -r -d '' TC_SYSTEM <<'__TC_SYSTEM__'
SYSTEM: Profile=Conversational Guidance
POLICY: Cite or abstain; follow Plan→Verify→Answer; ask ONE crisp follow-up if required.
...
__TC_SYSTEM__
printf %s 'Summarize the attached doc and list 3 risks.' | llm -m anthropic:claude-3-5-sonnet --system "$TC_SYSTEM" --no-stream
```

### Template types (input modes)

- **`arg`** (OpenAI): User input passed via bash here-string (`<<<`)
- **`stdin`** (Anthropic): User input piped via `printf`
- **`file`** (Ollama): File path passed as argument

### Requirements

- **Linux + bash** (relies on here-strings and heredocs)
- **`llm` CLI** installed (`pipx install llm`)
- **API keys** configured:
  - `OPENAI_API_KEY` for OpenAI models
  - `ANTHROPIC_API_KEY` for Anthropic models
  - Ollama requires local installation (`ollama pull llama3`)

### Why heredoc?

The heredoc approach (`<<'__TC_SYSTEM__'`) is:
- **Robust**: Handles newlines, quotes, `$`, backticks, and emoji without escaping
- **Safe**: No shell injection possible (literal mode)
- **Standard**: Works on any Linux/bash system
- **No limits**: Avoids command-line length restrictions
- **No conflicts**: Uses `TC_SYSTEM` variable to avoid conflicts with your existing shell variables

### Adding custom templates

1. Create a YAML file in `llm_templates/`:

```yaml
id: custom_model_chat
label: "Custom: My Model (chat)"
model: "custom:my-model"
description: "Chat completion via custom provider"
engine: "llm"
input_mode: "arg"
extra_flags: []
cmd_template: |
  {{SYS_HEREDOC}}
  llm -m {{MODEL}} --system "$SYS" {{INPUT_FRAGMENT}}
```

2. Regenerate the SPA:

```bash
python scripts/spa/generate_spa.py --root . --output capsule_composer.html
```

3. Refresh the SPA in your browser — your template will appear in the dropdown

---

## 16) Minimal Python wrapper (if you need it)

If you prefer to call `llm` from Python without learning any client SDKs right now:

```python
import subprocess, textwrap, pathlib

sys_prompt = pathlib.Path("demos/redteam/prompt.txt").read_text()
user_msg = "Give me a 6-bullet red-team assessment."

out = subprocess.run(
    ["llm", "-m", "openai:gpt-4o-mini", "--system", sys_prompt, user_msg],
    capture_output=True, text=True, check=True
).stdout

print(out)
```
