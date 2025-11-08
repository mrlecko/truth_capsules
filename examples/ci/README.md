
# CI Examples for Truth Capsules

This folder shows how to use Truth Capsules in CI (GitHub Actions). Two main patterns:

1. **Lint-only gate** - keep the library healthy.
2. **Compose-and-export** - produce a versioned system prompt + manifest from bundles and profiles.
3. **(Optional)** LLM judge gate - run a scoring model to enforce a rubric (requires an API key).

See `.github/workflows/` for ready-made workflows.

## Local usage

```bash
python capsule_linter.py truth-capsules-v1/capsules
python compose_capsules_cli.py --root truth-capsules-v1 \  --profile profile.ci_deterministic_gate_v1 \  --bundle pr_review_minibundle_v1 \  --out examples/ci/prompt.txt --manifest examples/ci/prompt.manifest.json
```
