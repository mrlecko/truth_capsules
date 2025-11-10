# Security Policy

## Reporting Vulnerabilities

We take security seriously. If you discover a security vulnerability in Truth Capsules:

- **DO NOT** open a public GitHub issue
- Report privately via GitHub Security Advisories or email the maintainer
- Include:
  - Description of the vulnerability
  - Steps to reproduce
  - Potential impact
  - Suggested fix (if any)

## Security Practices

### No Secrets in Repository

- Private keys are **never** committed to the repository
- The `keys/` directory is git-ignored (see `.gitignore`)
- Keys should be generated locally or dynamically in CI
- Demo keys for documentation should be clearly marked as non-production

### Witness Execution Sandbox

When running witness code via `run_witnesses.py`:

- Witnesses execute in process isolation
- No network access
- Read-only filesystem access
- Time and memory limits enforced
- See [WITNESSES_GUIDE.md](witnesses/WITNESSES_GUIDE.md) for security considerations

### Dependency Management

- Dependencies are pinned in `requirements.txt`
- Dependabot monitors for known vulnerabilities
- Regular security audits via `pip-audit` or similar tools

### Signing & Verification

- Capsule signing uses Ed25519 (strong cryptographic signatures)
- Signatures verify provenance and integrity
- Public keys are documented in provenance metadata
- See [PROVENANCE_SIGNING.md](misc/PROVENANCE_SIGNING.md) for details

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Security Best Practices for Users

1. **Verify signatures** before trusting capsules from external sources
2. **Review witness code** before execution (it runs arbitrary code)
3. **Use CI validation** to enforce security policies
4. **Pin versions** in production manifests
5. **Audit provenance** metadata for compliance requirements

## Contact

For security concerns: See repository maintainer contact in README.md


# Security & CSP Guide (HTML SPA Specific)

This repo ships a static SPA (`capsule_composer.html`) that loads embedded YAML data and renders text. To reduce risk:

## Static hosting recommendations
- Serve from a static host (e.g., GitHub Pages, Netlify) with a strict **Content Security Policy**.
- Do **not** allow inline scripts; the SPA uses a single self-contained script.

### Suggested CSP (adjust paths as needed)
```
Content-Security-Policy:
  default-src 'none';
  img-src 'self' data:;
  style-src 'self' 'unsafe-inline';
  script-src 'self';
  connect-src 'self';
  frame-ancestors 'none';
  base-uri 'none';
```
Notes:
- `style-src 'unsafe-inline'` is used sparingly for small CSS; consider hashing if you split JS/CSS.
- No external network calls; `connect-src 'self'` is conservative.

## Sanitization
- The SPA renders **text only** for YAML contents and escapes HTML.
- Avoid loading untrusted remote capsules; prefer locally curated files via source control.

## Reporting
- Report security issues privately first (see repository contacts).
