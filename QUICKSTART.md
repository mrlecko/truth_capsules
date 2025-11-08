# Quickstart

Get started with Truth Capsules in 5 minutes.

## Prerequisites

- Python 3.11+
- PyYAML (`pip install pyyaml`)

## 1. Lint Capsules

Validate all capsules for schema compliance:

```bash
python capsule_linter.py truth-capsules-v1/capsules
```

Expected output: `Capsules: 24  errors: 0  warnings: 0`

### Strict Mode

Require `approved` status for production use:

```bash
python capsule_linter.py truth-capsules-v1/capsules --strict
```

## 2. List Available Profiles and Bundles

```bash
# See all profiles and their aliases
python compose_capsules_cli.py --root truth-capsules-v1 --list-profiles

# See all bundles
python compose_capsules_cli.py --root truth-capsules-v1 --list-bundles
```

## 3. Compose Your First Prompt

### Example 1: Conversational Red Team Bundle

```bash
python compose_capsules_cli.py \
  --root truth-capsules-v1 \
  --profile conversational \
  --bundle conversation_red_team_baseline_v1 \
  --out examples/conversation_prompt.txt \
  --manifest examples/conversation_manifest.json
```

This creates a prompt with:
- 10 capsules focused on reasoning, red-teaming, and safety
- Natural language output format
- Socratic prompts for critical thinking

### Example 2: PR Review Bundle

```bash
python compose_capsules_cli.py \
  --root truth-capsules-v1 \
  --profile conversational \
  --bundle pr_review_minibundle_v1 \
  --out examples/pr_review_prompt.txt \
  --manifest examples/pr_review_manifest.json
```

This creates a prompt for code review with capsules for:
- Diff-first analysis
- Risk tagging (auth, I/O, concurrency, migrations)
- Test hints
- Deploy checklist
- Change impact assessment

### Example 3: CI Gate (Non-LLM)

```bash
python compose_capsules_cli.py \
  --root truth-capsules-v1 \
  --profile ci_det \
  --bundle ci_nonllm_baseline_v1 \
  --out examples/ci_gate_prompt.txt \
  --manifest examples/ci_gate_manifest.json
```

This creates a JSON-output prompt for deterministic CI checks.

## 4. View Composed Output

```bash
cat examples/conversation_prompt.txt
```

You'll see:
- Profile header (SYSTEM, POLICY, FORMAT)
- Capsule rules with statements, assumptions, and pedagogy
- Enforcement guidelines

## 5. Use with an LLM

### With Claude (API)

```python
import anthropic

client = anthropic.Client(api_key="your-key")

with open("examples/conversation_prompt.txt") as f:
    system_prompt = f.read()

response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    system=system_prompt,
    messages=[{"role": "user", "content": "Evaluate the claim: AI will replace all programmers by 2026"}]
)

print(response.content[0].text)
```

### With OpenAI (API)

```python
from openai import OpenAI

client = OpenAI(api_key="your-key")

with open("examples/conversation_prompt.txt") as f:
    system_prompt = f.read()

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Evaluate the claim: AI will replace all programmers by 2026"}
    ]
)

print(response.choices[0].message.content)
```

## 6. Explore the SPA (Optional)

Open `capsule_composer.html` in a browser to visually explore capsules, bundles, and profiles.

**Note:** The SPA contains a frozen data snapshot from generation time.

To regenerate with latest capsules:

```bash
python spa/generate_spa.py --root truth-capsules-v1 --output capsule_composer.html
```

See [spa/README.md](./scripts/spa/README.md) for details.

## 7. Sign Capsules (Optional)

Generate Ed25519 keys and sign capsules for provenance:

```bash
# Generate keys (example only - use a secure key management system in production)
python -c "from nacl.signing import SigningKey; sk = SigningKey.generate(); print('Private:', sk.encode().hex()); print('Public:', sk.verify_key.encode().hex())"

# Sign capsules
python capsule_sign.py truth-capsules-v1/capsules \
  --key "$PRIVATE_KEY_B64" \
  --pub "$PUBLIC_KEY_B64" \
  --key-id "prod-v1"

# Verify signatures
python capsule_verify.py truth-capsules-v1/capsules
```

## Next Steps

- Read [Capsule Schema v1](./docs/CAPSULE_SCHEMA_v1.md) to create your own capsules
- Explore [Profiles Reference](./docs/PROFILES_REFERENCE.md) to understand profile options
- Check [CI Guide](./docs/CI_GUIDE.md) to integrate capsules into your workflows
- Review [Security & CSP Guide](./docs/SECURITY_CSP.md) for production deployment

## Troubleshooting

### "Profile not found" error

Use `--list-profiles` to see available options. You can use either the alias (e.g., `conversational`) or full ID (e.g., `profile.conversational_guidance_v1`).

### "Bundle not found" error

Use `--list-bundles` to see available bundles. Bundle names are defined in the YAML `name` field, not the filename.

### Unicode escape sequences in capsules

If you see warnings about `\u2265`, run:

```bash
python fix_unicode_escapes.py truth-capsules-v1/capsules
```

This converts escape sequences (e.g., `\u2265`) to actual UTF-8 characters (e.g., `≥`).
