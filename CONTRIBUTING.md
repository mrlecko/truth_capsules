# Contributing

Thanks for your interest! This v1 is a **sponsor/hire demo**; contributions are welcome via issues or PRs.

## How to contribute
1. Open an issue first for significant changes.
2. For capsules: follow [Capsule Schema v1](docs/CAPSULE_SCHEMA_v1.md) and include **provenance**.
3. Run `python capsule_linter.py truth-capsules-v1/capsules` and ensure **no errors**.
4. If you add/modify bundles or profiles, update docs and examples where relevant.
5. For security-sensitive changes, see [Security & CSP](docs/SECURITY_CSP.md).

## Coding standards
- Python 3.11+; use `pyyaml` only.
- Keep CLI output deterministic for CI.
- Avoid network calls in examples; keep fixtures tiny.

## License
By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).
