# PR Review

Summary:
- Implements token refresh fix; adds cache on hot path; updates README; adds unit tests.

Tags: security, performance, docs, tests

Notes:
- Security: token refresh now checks expiry and avoids logging tokens.
- Performance: memoized expensive lookup; added 30s cache; measured ~25% latency drop in local bench.
- Docs: updated README with new env variable; linked to upgrade notes.
- Tests: added tests for expired token case and cache hit/miss behavior.
