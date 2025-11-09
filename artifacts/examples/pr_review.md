# Review Notes

Risks observed: auth, net, fs, secrets, pii

- **auth** — Mitigation: keep endpoint behind feature flag, require MFA for admin.
- **net** — Mitigation: set retry/backoff + circuit breaker; denylist external domains.
- **fs** — Mitigation: restrict paths to temp dir; add unit test to assert no absolute writes.
- **secrets** — Mitigation: remove hardcoded password; load from secret manager.
- **pii** — Mitigation: redact emails in logs and outputs; add unit test for redaction.

LGTM once mitigations are verified in follow-up PR.
