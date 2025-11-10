# WITNESS_SANDBOX

Run capsule **witnesses** inside a locked-down container so untrusted witness code can’t poke your host. This doc explains **why** the sandbox exists, **how** it works, and gives an **idiot-proof** command set (PASS/FAIL/SKIP demos included).

---

## TL;DR (5 commands)

```bash
# 1) Build the runner image (once)
make sandbox-build
# 2) PASS demo (PR Risk Tags)
make witness-sandbox CAPSULE=llm.pr_risk_tags_v1 WITNESS=pr_review_covers_risks JSON=1 \
  ENV_VARS='-e REVIEW_PATH=artifacts/examples/pr_review.md -e DIFF_PATH=artifacts/examples/pr_diff.patch'
# 3) FAIL demo (missing mitigations)
make witness-sandbox CAPSULE=llm.pr_risk_tags_v1 WITNESS=pr_review_covers_risks JSON=1 \
  ENV_VARS='-e REVIEW_PATH=artifacts/examples/pr_review_bad.md -e DIFF_PATH=artifacts/examples/pr_diff.patch'
# 4) PASS demo (Citations required)
make witness-sandbox CAPSULE=llm.citation_required_v1 WITNESS=citations_cover_claims JSON=1
# 5) FAIL + SKIP demos (citations)
make witness-sandbox CAPSULE=llm.citation_required_v1 WITNESS=citations_cover_claims JSON=1 \
  ENV_VARS='-e ANSWER_PATH=artifacts/examples/answer_with_citation_bad.json'
make witness-sandbox CAPSULE=llm.citation_required_v1 WITNESS=citations_cover_claims JSON=1 \
  ENV_VARS='-e DOC_CLASS=opinion'
```

> Results are printed as structured JSON; exit code `0` on PASS/SKIP, `1` on FAIL.

---

## Why a sandbox?

Witnesses are **executable artifacts** embedded in capsules (e.g., Python snippets). That’s powerful—but **risky** if you didn’t author them.

**Threat model (minimum):**

* Prevent witnesses from **writing to the repo** or snooping `$HOME`.
* Deny **network** egress.
* Limit **process** count and memory/CPU spikes.
* Make runs **reproducible**.

**This sandbox gives you:**

* **Read-only** bind mount of the repo into `/work`.
* **No network** (`--network=none`).
* **PIDs limit** (`--pids-limit=256`), non-root user inside the container.
* A tiny Python base with only what witnesses need.

> It’s a **PoC sandbox**, not a full governance product, but it’s a good default posture for sharing/CI.

---

## How it works

* `container/Dockerfile.runner` produces an image (default tag: `truthcapsules/runner:0.1`).
* Image `ENTRYPOINT` is `["python3"]` so we can run repo scripts by **path** (no “double python” foot-gun).
* `make witness-sandbox` runs:

  * `docker run --rm -t`
  * `--network=none --pids-limit=256`
  * `-v "$PWD":/work:ro -w /work`
  * pass any **ENV** required by the witness
  * execute `scripts/run_witnesses.py` with your `--capsule` / `--witness` selection

---

## Prereqs

* Docker (or Podman—see “Podman” note below)
* Repo has `scripts/run_witnesses.py` and example fixtures under `artifacts/examples/`

---

## Build the runner image

```bash
# Builds container/Dockerfile.runner
make sandbox-build
```

If you need to bump the tag, set `SANDBOX_IMAGE` when calling make:

```bash
make sandbox-build SANDBOX_IMAGE=myorg/tc-runner:dev
```

---

## Run witnesses in the sandbox (Makefile)

**PASS (PR Risk-Coverage)**

```bash
make witness-sandbox CAPSULE=llm.pr_risk_tags_v1 WITNESS=pr_review_covers_risks JSON=1 \
  ENV_VARS='-e REVIEW_PATH=artifacts/examples/pr_review.md -e DIFF_PATH=artifacts/examples/pr_diff.patch'
```

**FAIL (missing mitigations)**

```bash
make witness-sandbox CAPSULE=llm.pr_risk_tags_v1 WITNESS=pr_review_covers_risks JSON=1 \
  ENV_VARS='-e REVIEW_PATH=artifacts/examples/pr_review_bad.md -e DIFF_PATH=artifacts/examples/pr_diff.patch'
```

**PASS (Citations required)**

```bash
make witness-sandbox CAPSULE=llm.citation_required_v1 WITNESS=citations_cover_claims JSON=1
```

**FAIL (bad coverage)**

```bash
make witness-sandbox CAPSULE=llm.citation_required_v1 WITNESS=citations_cover_claims JSON=1 \
  ENV_VARS='-e ANSWER_PATH=artifacts/examples/answer_with_citation_bad.json'
```

**SKIP (opinion piece)**

```bash
make witness-sandbox CAPSULE=llm.citation_required_v1 WITNESS=citations_cover_claims JSON=1 \
  ENV_VARS='-e DOC_CLASS=opinion'
```

**Run *all* witnesses for *all* capsules (firehose)**

```bash
make witness-sandbox JSON=1
```

> The target prints a friendly banner and the exact `docker run …` invocation it’s using.

---

## Run directly with Docker (without make)

```bash
docker run --rm -t \
  --network=none --pids-limit=256 \
  -v "$PWD":/work:ro -w /work \
  -e REVIEW_PATH=artifacts/examples/pr_review.md \
  -e DIFF_PATH=artifacts/examples/pr_diff.patch \
  truthcapsules/runner:0.1 \
  scripts/run_witnesses.py capsules --capsule llm.pr_risk_tags_v1 --witness pr_review_covers_risks --json
```

**Why no `python3` after the image?**
Your image’s `ENTRYPOINT` is already `python3`. Adding `python3` again causes the “double-python” error.

---

## Passing inputs

Witnesses usually read from files via ENV (e.g., `REVIEW_PATH`, `DIFF_PATH`, `ANSWER_PATH`). Use the `ENV_VARS` make var to pass them:

```bash
ENV_VARS='-e ANSWER_PATH=artifacts/examples/answer_with_citation.json'
```

**Write access?**
The repo is mounted **read-only**. If a witness needs a scratch area, mount a temp dir:

```bash
mkdir -p artifacts/scratch
make witness-sandbox JSON=1 \
  EXTRA_VOLUMES='-v $PWD/artifacts/scratch:/scratch:rw' \
  ENV_VARS='-e TC_TMP=/scratch'
```

---

## Status & exit codes

* **PASS** → witness `returncode=0`, capsule status **GREEN**, runner exits `0`
* **FAIL** → witness `returncode!=0`, capsule status **RED**, runner exits `1`
* **SKIP** → non-error skip (policy), runner exits `0`

JSON output includes a `stdout` payload from the witness with details.

---

## Common gotchas (and fixes)

* **“python3: can’t open file '/work/python3'”**
  You accidentally passed `python3` after an image with `ENTRYPOINT ["python3"]`. Drop the extra `python3`.

* **Witness needs network**
  By design, network is **off**. If you truly need it for a demo, remove `--network=none` (not recommended for untrusted code).

* **Writes fail**
  You’re on a **ro** mount. Provide a separate **rw** scratch mount (see “Passing inputs”).

* **Paths wrong**
  Remember the container’s working dir is `/work`. Use repo-relative paths in ENV.

---

## Advanced hardening (recommended knobs)

You can strengthen the default sandbox by adding (in Makefile or local override):

```bash
--read-only \
--cap-drop=ALL \
--security-opt=no-new-privileges \
--pids-limit=256 \
--memory=512m --cpus=1 \
--tmpfs /tmp:rw,size=64m,mode=1777 \
--mount type=bind,src="$PWD",dst=/work,ro \
--mount type=tmpfs,dst=/var/tmp,tmpfs-mode=1777,tmpfs-size=64m
```

> For extra credit: provide a dedicated **seccomp** profile and (on Linux) an **AppArmor** profile.

---

## CI usage (GitHub Actions)

```yaml
name: witnesses
on: [push, pull_request]
jobs:
  run-witnesses:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build sandbox runner
        run: make sandbox-build
      - name: Run PR Risk witness
        run: |
          make witness-sandbox CAPSULE=llm.pr_risk_tags_v1 WITNESS=pr_review_covers_risks JSON=1 \
            ENV_VARS='-e REVIEW_PATH=artifacts/examples/pr_review.md -e DIFF_PATH=artifacts/examples/pr_diff.patch'
      - name: Run Citations witness
        run: |
          make witness-sandbox CAPSULE=llm.citation_required_v1 WITNESS=citations_cover_claims JSON=1
```

---

## Podman users

Set the engine once:

```bash
make sandbox-build SANDBOX_ENGINE=podman
make witness-sandbox SANDBOX_ENGINE=podman CAPSULE=... WITNESS=... JSON=1
```

---

## Troubleshooting

* **See the exact docker command:** every `make witness-sandbox` run prints it.
* **Interactive shell in the image:**

  ```bash
  docker run --rm -it -v "$PWD":/work:ro -w /work --network=none truthcapsules/runner:0.1 /bin/sh
  ```
* **Time limits:** witnesses manage their own timeouts; for global limits, wrap the docker run in `timeout 15s …`.
* **Rebuild image after Dockerfile changes:**

  ```bash
  make sandbox-build --always-make
  ```

---

## Security posture recap

This PoC sandbox:

* isolates witness execution in a container,
* blocks network, runs as non-root,
* constrains process count,
* keeps your repo read-only.

It **does not** guarantee perfect isolation. For adversarial code or regulated environments, graduate to:

* locked-down seccomp/AppArmor profiles,
* read-only root + whitelisted tmpfs,
* cgroup limits,
* per-witness OCI bundles or Firecracker/VM-based sandboxes.

---

## Appendix: Makefile knobs you can override

* `SANDBOX_IMAGE` (default `truthcapsules/runner:0.1`)
* `SANDBOX_ENGINE` (`docker` or `podman`)
* `ENV_VARS` (e.g., `-e KEY=VAL -e OTHER=VAL`)
* `EXTRA_VOLUMES` (e.g., `-v $PWD/artifacts/scratch:/scratch:rw`)
* `JSON=1` (pretty JSON output)

Example:

```bash
make witness-sandbox \
  SANDBOX_IMAGE=myorg/tc-runner:sha-abc123 \
  ENV_VARS='-e ANSWER_PATH=artifacts/examples/answer_with_citation.json' \
  EXTRA_VOLUMES='-v $PWD/artifacts/scratch:/scratch:rw' \
  CAPSULE=llm.citation_required_v1 WITNESS=citations_cover_claims JSON=1
```