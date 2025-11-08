# Task

Assess the below feedback on the current repository layout and "hygiene"

Implement the suggested changes if you agree with the action - if not do not implement the changes and report why that aspect was omitted at the end of the implementation process. 

Create a plan to review, then action the below

---

Short take: your layout is solid-clear separation of `capsules/`, `bundles/`, `profiles/`, `schemas/`, `scripts/`, docs, examples, and CI. It’s already more “real” than most repos. The gaps now are reproducibility, lint/test scaffolding, security hygiene, and release polish.

Here’s what I’d add (prioritized):

## Must-add / fix

1. **Remove committed private key & ignore keys directory**

   * Replace `keys/demo_ed25519_sk.pem` with a README and ignore real keys.
   * Commands:

     ```bash
     git rm --cached keys/demo_ed25519_sk.pem
     git commit -m "Remove demo private key from repo"
     ```
   * Update `.gitignore` (see snippet below).

2. **Tests scaffold**

   * Add `tests/` with schema validation + script sanity tests.
   * Minimal structure:

     ```
     tests/
       test_capsules_validate.py
       fixtures/
         capsules/…           # copy a couple from /capsules
         schemas/…            # link or import from /schemas
     ```

3. **Pre-commit hooks (style + safety)**

   * `.pre-commit-config.yaml` with: `ruff`, `black`, `isort`, `yamllint`, `markdownlint`, `check-jsonschema`, `detect-secrets`, `end-of-file-fixer`, `trailing-whitespace`.

4. **Editor & line-ending normalization**

   * `.editorconfig` and `.gitattributes` so YAML/JSON stay LF and diffs are nice.

5. **CHANGELOG + version stamp**

   * `CHANGELOG.md` (Keep a Changelog), and a `VERSION` file (e.g., `1.0.0-rc1`) or `pyproject.toml` with a project version.

6. **Security policy**

   * `SECURITY.md` (how to report vulns), plus add a quick “no secrets” policy to CONTRIBUTING.

## Strongly recommended

7. **Pin & lock dependencies**

   * Keep `requirements.in` (human) → compiled `requirements.txt` (pinned) via pip-tools **or** switch to `pyproject.toml` + `uv`/`poetry`. Include a `constraints.txt` for CI.

8. **Makefile (or justfile)**

   * One-liners for `setup`, `lint`, `test`, `sign`, `verify`, `compose`, `ci`.

9. **Dependabot / Renovate**

   * `.github/dependabot.yml` to bump actions and Python deps.

10. **CodeQL (or Bandit)**

* Add a GitHub Actions workflow for static analysis (lightweight win).

11. **Dockerfile / devcontainer (optional but helpful)**

* Reproducible local+CI runs for `scripts/run_capsules.py` and signing/verification.

12. **YAML style guidance**

* `docs/STYLE_YAML.md` or a short section in `LINTER_GUIDE.md` (block literals for code, `|-` vs `|+`, 2-space indents, UTF-8).

---

## Minimal file snippets to drop in

### .gitignore (augment yours)

```gitignore
# Python
__pycache__/
*.pyc
.venv/
.venv*/
.env
.env.*
.pytest_cache/
.coverage
htmlcov/

# Node (if any)
node_modules/

# OS/IDE
.DS_Store
Thumbs.db
.vscode/
.idea/

# Build & wheels
dist/
build/
*.egg-info/

# Artifacts & outputs (keep examples/)
artifacts/out/
artifacts/*.log

# Keys / secrets
keys/*.pem
keys/*.key
keys/*.pub
keys/.secrets/
!keys/README.md
```

### keys/README.md

````md
# Keys

No private keys should be committed.

- Generate a demo key locally when needed:
  ```bash
  ssh-keygen -t ed25519 -N "" -f keys/local_demo_ed25519_sk.pem
````

* Reference the public key in `PROVENANCE_SIGNING.md`.
* CI should mint throwaway keys for test signing.

````

### .editorconfig
```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
indent_style = space
indent_size = 2
trim_trailing_whitespace = true

[*.py]
indent_size = 4

[Makefile]
indent_style = tab
````

### .gitattributes

```gitattributes
* text=auto eol=lf
*.yaml diff
*.yml  diff
*.json linguist-language=JSON
*.md   diff=markdown
```

### .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.10.0
    hooks: [{id: black}]
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.7.2
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks: [{id: isort}]
  - repo: https://github.com/adrienverge/yamllint
    rev: v1.35.1
    hooks: [{id: yamllint}]
  - repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.41.0
    hooks: [{id: markdownlint}]
  - repo: https://github.com/python-jsonschema/check-jsonschema
    rev: 0.29.4
    hooks:
      - id: check-jsonschema
        files: "^capsules/.*\\.ya?ml$"
        args: ["--schemafile", "schemas/judge.schema.v1.json"]  # adjust per folder
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks: [{id: detect-secrets}]
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace
```

### tests/test_capsules_validate.py (example)

```python
import glob, json, subprocess, sys, yaml, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
CAPSULES = ROOT / "capsules"

def test_all_capsules_lint_and_validate():
    # 1) yamllint via pre-commit config (optional)
    # 2) basic schema presence + witnesses block literal style
    for path in glob.glob(str(CAPSULES / "*.yaml")):
        with open(path, "r", encoding="utf-8") as f:
            doc = yaml.safe_load(f)
        assert "id" in doc or "name" in doc
        if "witnesses" in doc:
            for w in doc["witnesses"]:
                assert "language" in w
                assert ("code" in w) ^ ("code_ref" in w)
```

### Makefile

```makefile
.PHONY: setup lint test sign verify compose ci

PY=python3

setup:
	$(PY) -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -r requirements.txt && pre-commit install

lint:
	pre-commit run --all-files

test:
	pytest -q

sign:
	$(PY) scripts/capsule_sign.py --in capsules --out capsules

verify:
	$(PY) scripts/capsule_verify.py --in capsules

compose:
	$(PY) scripts/compose_capsules_cli.py --bundles bundles --out artifacts/out

ci: lint test verify compose
```

### CHANGELOG.md

```md
# Changelog
All notable changes to this project will be documented here.

## [1.0.0-rc1] - 2025-11-07
- Initial public RC: capsule schema v1, baseline bundles, CI, linter, witness runner.
```

### SECURITY.md

```md
# Security Policy

- Please do not open public issues for vulnerabilities.
- Report privately to security@yourdomain.example (PGP optional).
- No secrets in repo (see `.gitignore`); keys are generated locally or in CI.
- Witness code runs in a sandbox: no network, RO filesystem, time/memory limits.
```

### .github/dependabot.yml

```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule: { interval: "weekly" }
  - package-ecosystem: "pip"
    directory: "/"
    schedule: { interval: "weekly" }
```

---

## Sanity check on current tree

* **Sane & navigable?** Yes. Folders map intuitively to concepts; CI is present; docs are rich. 👍
* **Minor tweaks:**

  * Add `docs/index.md` to serve as a table of contents.
  * Consider moving Python into a `src/` package (`src/truthcapsules/…`) if scripts are growing, with console entry points for `compose`, `sign`, `verify`.
  * Add `artifacts/README.md` clarifying which files are example inputs vs generated outputs (and keep generated stuff out of Git).
  * Add `docs/STYLE_YAML.md` or extend `LINTER_GUIDE.md` with the block-literal rules for `witnesses`.

If you want, I can generate these files tailored to your exact schema names (e.g., wiring `check-jsonschema` to the right schemas per folder) and a first `tests/` pass that loads all capsules and validates witness fields.
