# SIGNED_WITNESSES.md

A concise, reproducible guide to **run a witness in a sandbox**, **sign the results**, and **verify the receipts**. Includes both a failing (**RED**) and passing (**GREEN**) case.

---

## What you get

* **Witness results** as raw JSON
* A **cryptographically signed envelope** covering the canonicalized results
* A **detached signature** for tooling that prefers sidecar `.sig` files
* A simple **verifier** script (and an OpenSSL-only path) so anyone can check the receipts

---

## Prerequisites

* Docker available (default sandbox engine).
* Repo root mounted read-only inside the runner by the Makefile target `witness-sandbox`.
* Ed25519 signing key at `keys/dev_ed25519_sk.pem` (or set `SIGNING_KEY=...`).
* Public key extracted once for verification:

  ```bash
  openssl pkey -in keys/dev_ed25519_sk.pem -pubout > keys/dev_ed25519_pk.pem
  ```

### Key paths used in examples

* **RED** input (bad citations): `artifacts/examples/answer_with_citation_bad.json`
* **GREEN** input (good citations): `artifacts/examples/answer_with_citation.json`
* Signing output directory: `artifacts/out/`

---

## 1) Run + Sign (RED)

This demonstrates a failing run that still produces signed receipts.

```bash
make witness-sandbox CAPSULE=llm.citation_required_v1 WITNESS=citations_cover_claims JSON=1 \
  ENV_VARS="-e ANSWER_PATH=artifacts/examples/answer_with_citation_bad.json" \
  SIGN=1 SIGNING_KEY=keys/dev_ed25519_sk.pem KEY_ID=john@truthcapsules
```

**What happens:**

* The sandbox executes the witness and prints the raw JSON array to stdout (status will be `RED`).
* Three files are written under `artifacts/out/`:

  * `witness_<UTCSTAMP>.json`               ← raw results (verbatim)
  * `witness_<UTCSTAMP>.signed.json`        ← results + `proof` block (signature & digest)
  * `witness_<UTCSTAMP>.sig`                ← detached signature (base64)

> Tip: If you’re demoing and want the shell to exit 0 even on RED, add `ALLOW_RED=1` at the end of the `make` command.

---

## 2) Run + Sign (GREEN)

This uses the good example and should pass.

```bash
make witness-sandbox CAPSULE=llm.citation_required_v1 WITNESS=citations_cover_claims JSON=1 \
  ENV_VARS="-e ANSWER_PATH=artifacts/examples/answer_with_citation.json" \
  SIGN=1 SIGNING_KEY=keys/dev_ed25519_sk.pem KEY_ID=john@truthcapsules
```

Expected: witness status is **GREEN**, and the same three artifacts are emitted under `artifacts/out/`.

---

## 3) Verify the Signed Envelope (simple path)

Use the included verifier:

```bash
# Pick the newest signed envelope
SIGNED=$(ls -t artifacts/out/witness_*.signed.json | head -n1)

# Verify (digest + Ed25519 signature on canonical JSON)
python3 scripts/verify_witness.py "$SIGNED" keys/dev_ed25519_pk.pem
# → OK (on success)
```

What this does:

* Recomputes **canonical JSON** of `results` (sorted keys, minimal separators, UTF-8).
* Checks the embedded **SHA-256 digest**.
* Verifies the **Ed25519 signature** over those canonical bytes using your public key.

---

## 4) Verify with OpenSSL only (advanced, no helper script)

```bash
SIGNED=$(ls -t artifacts/out/witness_*.signed.json | head -n1)

# Extract the "results" array from the signed doc
python3 - <<'PY' > /tmp/results.json
import sys, json
signed = json.load(open(sys.argv[1]))
json.dump(signed["results"], sys.stdout, sort_keys=True, separators=(',',':'), ensure_ascii=False)
PY "$SIGNED"

# Base64 decode the in-document signature to /tmp/sig.bin
python3 - <<'PY' > /tmp/sig.bin
import sys, json, base64
signed = json.load(open(sys.argv[1]))
print(base64.b64decode(signed["proof"]["signature"]).decode("latin1"), end="")
PY "$SIGNED"

# Verify: Ed25519 raw verify on canonical bytes of results
openssl pkeyutl -verify -pubin -inkey keys/dev_ed25519_pk.pem \
  -rawin -in /tmp/results.json -sigfile /tmp/sig.bin
# → Signature Verified Successfully
```

---

## 5) Artifact Structure

Example of `witness_<ts>.signed.json`:

```json
{
  "results": [
    {
      "capsule": "llm.citation_required_v1",
      "status": "GREEN",
      "witness_results": [
        {
          "name": "citations_cover_claims",
          "status": "PASS",
          "returncode": 0,
          "stdout": "{\"witness\":\"citations_cover_claims\",\"status\":\"PASS\",...}\n",
          "stderr": ""
        }
      ]
    }
  ],
  "proof": {
    "type": "Ed25519",
    "created": "2025-11-09T23:16:23Z",
    "keyId": "john@truthcapsules",
    "canonical": {
      "algo": "json-c14n-v1",
      "hash": "sha256",
      "digest": "<sha256 of canonical(results)>"
    },
    "signature": "<base64(Ed25519 signature over canonical(results))>",
    "meta": {
      "engine": "sandbox",
      "image": "truthcapsules/runner:0.1",
      "git": "<optional short sha>"
    }
  }
}
```

**Important notes**

* The **signature covers only `results`** (not the `proof` metadata) to keep verification stable.
* Canonicalization is the exact `json.dumps(..., sort_keys=True, separators=(',', ':'), ensure_ascii=False)` of the `results` array.
* Ed25519 signatures are deterministic for a given `(message, key)`, so if the results are identical and you use the same private key, the signature is the same across runs.

---

## 6) Exit Codes & CI

* By default, a **RED** run exits non-zero (good for CI).
* For demos and docs that must continue, append `ALLOW_RED=1` to the `make` command to absorb the non-zero exit while still writing all receipts.
* The signing step is **non-fatal**: if signing fails, the raw JSON still prints to stdout and the command’s exit reflects only the witness result (unless `ALLOW_RED=1`).

---

## 7) Reproducibility Checklist

* **Determinism**: If the capsule + inputs are unchanged and the witness is deterministic, re-running will:

  * Produce the **same canonical JSON** for `results`
  * Yield the **same digest**
  * Produce the **same Ed25519 signature** with the same key
* **Receipts**: Every run yields a verifiable trail (`.json`, `.signed.json`, `.sig`) so reviewers can re-check without access to your environment.

---

## 8) Troubleshooting

* **“Permission denied” or file not found in runner**
  Ensure the Makefile mounts the repo read-only at `/work` and uses `/bin/sh -lc 'python3 scripts/run_witnesses.py ...'`. The provided `witness-sandbox` target handles this.

* **“invalid JSON: empty input” during signing**
  This happens if a shell expansion swallowed the runner output. The Makefile now captures runner stdout into `OUT_JSON` and feeds a temporary file to the signer—use the provided target as-is.

* **Want to force GREEN/RED for demos**
  Use the provided example inputs:

  * GREEN: `artifacts/examples/answer_with_citation.json`
  * RED:   `artifacts/examples/answer_with_citation_bad.json`

---

## 9) One-shot Demo Script (copy/paste)

```bash
# RED (fails), sign, verify
make witness-sandbox CAPSULE=llm.citation_required_v1 WITNESS=citations_cover_claims JSON=1 \
  ENV_VARS="-e ANSWER_PATH=artifacts/examples/answer_with_citation_bad.json" \
  SIGN=1 SIGNING_KEY=keys/dev_ed25519_sk.pem KEY_ID=john@truthcapsules ALLOW_RED=1
SIGNED=$(ls -t artifacts/out/witness_*.signed.json | head -n1)
python3 scripts/verify_witness.py "$SIGNED" keys/dev_ed25519_pk.pem

# GREEN (passes), sign, verify
make witness-sandbox CAPSULE=llm.citation_required_v1 WITNESS=citations_cover_claims JSON=1 \
  ENV_VARS="-e ANSWER_PATH=artifacts/examples/answer_with_citation.json" \
  SIGN=1 SIGNING_KEY=keys/dev_ed25519_sk.pem KEY_ID=john@truthcapsules
SIGNED=$(ls -t artifacts/out/witness_*.signed.json | head -n1)
python3 scripts/verify_witness.py "$SIGNED" keys/dev_ed25519_pk.pem
```

---

## 10) FAQ

**Q: What exactly is being signed?**
A: The **canonical JSON bytes** of the `results` array (not the `proof` block). The signature and digest attest to those bytes.

**Q: Why canonicalization?**
A: To ensure the same semantic results produce byte-identical input to the signature algorithm, independent of incidental whitespace or map ordering.

**Q: Can I verify without any repo scripts?**
A: Yes — the OpenSSL-only path above verifies the signature using only the signed JSON, your public key, and two short Python one-liners to extract bytes and decode the signature.