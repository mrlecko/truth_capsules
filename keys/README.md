# Keys Directory

**IMPORTANT:** No private keys should be committed to this repository.

## Generating Keys Locally

For testing or local signing, generate an Ed25519 key pair:

```bash
# Generate a demo key (Ed25519)
ssh-keygen -t ed25519 -N "" -f keys/local_demo_ed25519_sk.pem

# Or use OpenSSL
openssl genpkey -algorithm ED25519 -out keys/local_demo_ed25519_sk.pem
```

## CI/CD Key Management

- CI workflows should generate throwaway keys for test signing
- Production keys should be stored in secure secret management (GitHub Secrets, HashiCorp Vault, etc.)
- Never commit production keys to version control

## Key Usage

- **Signing capsules:** See [PROVENANCE_SIGNING.md](../docs/PROVENANCE_SIGNING.md)
- **Public keys:** Reference public keys in capsule `provenance.signing.pubkey` field
- **Verification:** Use `capsule_verify.py` with public keys

## Security Note

All files in this directory are git-ignored except this README.
See `.gitignore` for details.
