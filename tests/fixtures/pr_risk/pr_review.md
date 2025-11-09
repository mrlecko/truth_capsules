# Review Notes

Risks observed: auth, net, fs, secrets

- **auth** — Mitigation: require MFA and feature flag on login path.
- **net** — Mitigation: retry/backoff + circuit breaker; restrict domains.
- **fs** — Mitigation: confine writes to temp dir; add unit tests.
- **secrets** — Mitigation: remove hardcoded password; use secret manager.
