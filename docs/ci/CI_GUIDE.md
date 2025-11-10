# CI Guide

This repo includes three GitHub Actions workflows:

- **capsules-lint** - run linter on every push/PR.
- **capsules-compose** - manual; composes a prompt + manifest from inputs.
- **capsules-llm-judge** - optional; stubs a model judge and enforces a threshold.

### Local
```bash
python capsule_linter.py truth-capsules-v1/capsules
python compose_capsules_cli.py --root truth-capsules-v1 --profile ci_nonllm_baseline_v1   --bundle pr_review_minibundle_v1 --out examples/ci/prompt.txt --manifest examples/ci/prompt.manifest.json
```
