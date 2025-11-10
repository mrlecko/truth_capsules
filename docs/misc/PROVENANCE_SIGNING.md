# Provenance & Signing

Capsules carry a `provenance` header to enable trust and traceability.

## Required fields
- **author**, **org**, **license**, **created**, **updated**
- **review**: status, reviewers, last_reviewed
- **signing**: method, key_id, pubkey, **digest**, signature (optional)

## Digest
The `digest` is SHA-256 over the core content (schema doc). It must match on CI.

## Signing
Use Ed25519 (optional). Scripts:
```bash
python capsule_sign.py truth-capsules-v1/capsules --key "$ED25519_SECRET_B64" --key-id "prod-key-2025-11" --pub "$ED25519_PUBLIC_B64"
python capsule_verify.py truth-capsules-v1/capsules
```

## CI recommendations
- Fail CI if `digest` mismatches.
- On release branches, require signature for capsules with `review.status=approved`.
