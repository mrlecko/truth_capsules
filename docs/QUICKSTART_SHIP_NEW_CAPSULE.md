Awesome—here’s a drop-in, “10 minutes to wow” guide you can ship as `docs/QUICKSTART_10_MINUTES.md` (or paste into your README). It’s opinionated, copy-pasteable, and walks from **new capsule → profile → witness → digest/sign → use it (CLI, sandbox, SPA, deeplink, and programmatic)**.

---

# Verification Capsules in 10 Minutes

**Reproducible checks. Receipts. Low ceremony.**

This quickstart shows how to:

1. Create a **new capsule**
2. Add a **profile** for prompt composition (SPA + CLI)
3. Implement a **basic witness** (deterministic check)
4. **Build & verify** the digest (and optionally sign)
5. **Consume** the capsule via CLI, **sandbox**, **SPA**, **deeplink**, and **programmatically**

> Assumptions: you’re at the repo root, have `python3` and `docker` available.

---

## 0) One-time setup (≈60s)

```bash
make setup             # venv + deps
make sandbox-image     # build the minimal runner image (no-net, RO FS, caps dropped)
```

---

## 1) Create a capsule (≈15s)

We’ll create a tiny “README quality” capsule that checks your `README.md` has at least **3 second-level headers** (`## `).

```bash
make scaffold \
  DOMAIN=demo \
  NAME=readme_quality_v1 \
  TITLE="README has basic sections" \
  STATEMENT="Project README has at least 3 '## ' sections." \
  WITNESS=has_min_sections
```

This creates a skeleton under:

```
capsules/demo/readme_quality_v1/
  capsule.yaml
  witnesses/has_min_sections.py
  README.md (template)
```

---

## 2) Implement a basic witness (≈60–90s)

Open `capsules/demo/readme_quality_v1/witnesses/has_min_sections.py` and replace with:

```python
#!/usr/bin/env python3
import json, os, sys, re, time
# Deterministic environment (best practice)
os.environ.setdefault("TZ", "UTC")

def main():
    t0 = time.time()
    readme = os.environ.get("README_PATH", "README.md")
    min_secs = int(os.environ.get("MIN_SECTIONS", "3"))

    try:
        with open(readme, "r", encoding="utf-8") as f:
            txt = f.read()
    except Exception as e:
        out = {
            "witness": "has_min_sections",
            "status": "FAIL",
            "reason": "input-not-found",
            "error": str(e),
            "inputs": {"readme": readme, "min_sections": min_secs},
        }
        print(json.dumps(out, sort_keys=True))
        sys.exit(1)

    sections = re.findall(r"(?m)^##\s+", txt)
    ok = len(sections) >= min_secs

    out = {
        "witness": "has_min_sections",
        "status": "GREEN" if ok else "FAIL",
        "reason": None if ok else "too-few-sections",
        "count": len(sections),
        "min": min_secs,
        "inputs": {"readme": readme},
        # small provenance (runner fills more when sandboxed)
        "duration_ms": int((time.time() - t0) * 1000),
    }
    print(json.dumps(out, sort_keys=True))
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
```

> **Contract:** Witnesses print **one JSON object** with `status ∈ {GREEN, FAIL, SKIP}` and exit `0(GREEN/SKIP) / 1(FAIL)`. The sandbox runner wraps these into a **capsule-level JSON array receipt**.

Make the script executable if needed:

```bash
chmod +x capsules/demo/readme_quality_v1/witnesses/has_min_sections.py
```

---

## 3) (Optional) Add a profile for the SPA & CLI composer (≈60s)

Create `profiles/demo_writer.json`:

```json
{
  "id": "demo_writer",
  "title": "Concise Technical Writer",
  "system": "You are a concise technical writer. Use active voice and numbered steps. Avoid hype; be exact.",
  "hints": [
    "Ask for missing inputs explicitly.",
    "Return a short summary and a bulleted checklist."
  ],
  "vars": {
    "tone": "neutral",
    "audience": "engineers"
  }
}
```

> Profiles are lightweight “prompt personas” the SPA/CLI can combine with capsules to emit **ready-to-use prompts + manifests**.

List profiles:

```bash
make list-profiles
```

---

## 4) Build the digest & verify (≈20–30s)

Create/refresh the aggregate capsule digest and verify it reproduces byte-for-byte:

```bash
make digest
make digest-verify    # rebuilds and checks equality (supply-chain sanity)
```

(Optionally) sign & verify the signed NDJSON:

```bash
make keygen                                       # dev keypair to ./keys
SIGNING_KEY=keys/dev_private.pem make sign        # -> artifacts/out/capsules.signed.ndjson
PUBLIC_KEY=keys/dev_public.pem make verify
```

---

## 5) Run the witness locally (simple mode)

### 5.a) Direct (no sandbox), JSON receipt

```bash
make run-witness CAP=demo.readme_quality_v1 WIT=has_min_sections \
  RUNENV='README_PATH=README.md MIN_SECTIONS=3' JSON=1
```

You should see a JSON list with one result; `status` is `GREEN` if your README has ≥3 `##`.

---

## 6) Run inside the sandbox (isolated, receipts) 🔒

**Recommended** for demos—no network, read-only mounts, caps dropped, tmpfs `/tmp`.

#### 6.a) Using an env file (easiest)

Create `artifacts/examples/readme.env`:

```
README_PATH=README.md
MIN_SECTIONS=3
```

Run:

```bash
make witness-sandbox CAPSULE=demo.readme_quality_v1 WITNESS=has_min_sections \
  JSON=1 ENV_FILE=artifacts/examples/readme.env
```

Example output (capsule-level receipt):

```json
[
  {
    "capsule": "demo.readme_quality_v1",
    "status": "GREEN",
    "witness_results": [
      {
        "name": "has_min_sections",
        "status": "GREEN",
        "returncode": 0,
        "stdout": "{\"count\":3,\"inputs\":{\"readme\":\"/work/README.md\"},\"min\":3,\"reason\":null,\"status\":\"GREEN\",\"witness\":\"has_min_sections\"}\n",
        "stderr": "",
        "provenance": {
          "engine": "docker",
          "image": "truthcapsules/runner:0.1@sha256:…",
          "flags": "--rm --user 1000:1000 --read-only …",
          "duration_ms": 120
        }
      }
    ]
  }
]
```

> **Exit codes:** runner returns `0` for `GREEN/SKIP`, `1` for `RED`, `2` for infra/runtime issues. Your tests can treat `(1|2)` as non-GREEN if desired.

---

## 7) Compose prompts & manifests (CLI + SPA + deeplinks)

### 7.a) CLI compose (prompt + manifest into `artifacts/out/`)

Compose a prompt+manifest pairing your new capsule with the writer profile:

```bash
make compose CAPSULE=demo.readme_quality_v1 PROFILE=demo_writer
# Outputs (example):
# artifacts/out/demo.readme_quality_v1+demo_writer.prompt.md
# artifacts/out/demo.readme_quality_v1+demo_writer.manifest.json
```

Peek:

```bash
sed -n '1,80p' artifacts/out/demo.readme_quality_v1+demo_writer.prompt.md
jq . artifacts/out/demo.readme_quality_v1+demo_writer.manifest.json
```

### 7.b) SPA (strict, embedded assets)

Generate the SPA (no external calls; pinned hashes):

```bash
make spa-strict
# => capsule_composer.html
```

Open `./capsule_composer.html` in a browser:

1. Pick **Capsules → demo.readme_quality_v1**
2. Pick **Profile → demo_writer**
3. Click **Compose**
4. Export:

   * **Manifest JSON** (download)
   * **Prompt markdown** (copy or download)
   * **Deeplink** (URL fragment encoding your selection)

> If you host the SPA (e.g., `docs/index.html` via GitHub Pages):
> `make spa-pages` → writes to `docs/` with the same strict embedding.

### 7.c) Deeplink pattern

From the SPA’s **Export → Deeplink**, you’ll get a URL like:

```
file:///…/capsule_composer.html#caps=…&profile=…&state=…
```

Share this link—opening it restores the selection, so teammates can re-compose the same prompt/manifest immediately.

---

## 8) Programmatic “LLM usage” (manifest-first) 🧩

Use the **manifest JSON** you just created to prime your favorite LLM client. Here’s a generic Python sketch that:

* loads the manifest
* inlines the profile’s “system” text
* emits a chat request payload (OpenAI-style)

```python
import json, os

MANIFEST = "artifacts/out/demo.readme_quality_v1+demo_writer.manifest.json"

with open(MANIFEST, "r", encoding="utf-8") as f:
    m = json.load(f)

system_text = m.get("profile", {}).get("system", "")
prompt = m.get("prompt", "Compose an answer using the capsule assumptions.")

payload = {
    "model": os.environ.get("LLM_MODEL", "gpt-4o-mini"),
    "messages": [
        {"role": "system", "content": system_text},
        {"role": "user", "content": prompt}
    ]
}

print(json.dumps(payload, indent=2))
# You can now send `payload` via your preferred client/library.
```

> If you maintain a local `llm` helper module, adapt the load/compose step there. The key is: **capsule + profile → deterministic manifest + prompt**, which you can pipe into any client.

---

## 9) Receipts & provenance (best practice)

* Keep the capsule-level JSON receipts from `witness-sandbox` under `artifacts/out/receipts/…`.
* They include runner provenance (`engine`, `image digest`, `flags`, `duration_ms`).
* Add them to your PRs/releases as **portable verification receipts**.

---

## 10) Troubleshooting (fast)

* **Exit code = 2** → infra (permissions, timeouts). Re-run with `JSON=1` to inspect `stderr`.
* **File not found** → prefer `ENV_FILE=…` over complex quoting in `ENV_VARS`.
* **Nondeterminism** → set `TZ=UTC LANG=C.UTF-8 PYTHONHASHSEED=0` (runner already sets sane defaults).
* **Sandbox writes** → witnesses must write only to `/tmp`; workdir is read-only.
* **SPA “Prism is not defined”** → use `make spa-strict` (embedded assets + pinned hashes); avoid mixed CDNs.

---

## 11) Clean up

```bash
make clean          # remove generated artifacts
make clean-venv     # remove .venv
```

---

### Why this matters (one paragraph)

Capsules let you **package verifiable claims** about artifacts/process as runnable checks with **reproducible receipts**. The sandbox gives you a minimal, inspectable isolation profile (no network, RO mounts, limits). Profiles + SPA/CLI give you **prompt/manifest composition** that’s deterministic and shareable (including deeplinks). Together, this makes “**reproducibility + receipts + low ceremony**” a habit, not a hope.

---

**That’s it.** You just shipped a new capsule, proved it in an isolated runner, and produced prompt/manifest outputs your teammates (or CI) can reuse immediately.
