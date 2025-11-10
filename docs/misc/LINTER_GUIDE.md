# Linter Guide

Run:
```bash
python capsule_linter.py truth-capsules-v1/capsules
```

The linter checks:
- Required fields: `id, version, domain, statement, provenance`
- Pedagogy structure: list of `{kind, text}` (kinds: Socratic, Aphorism)
- Provenance minimal set: `schema, author, license, created` and `signing.digest`

CI exits non-zero if any errors are present.
