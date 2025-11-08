# Problem

The current v1 release candidate doesn't sensibly support, demonstrate or document the idea of executionable "witnesses" which are in the schema

The idea is to attach python, javascript, any code artifact which can be executed in a sandbox / process the user controls (responsibility is on them to solve that trusted execution problem)

I want to update the current project to support that

there's currently a "run_capsules.py" file which is from the original version which the current example capsules are still in the schema of

the "pedagogy.problem_solving_v1.yaml" capsule contains an example of a witness

your task is to fully implement and sanity check the "code as witnesses" feature then update the docs to support this

below is guidance on how to use yaml to represent the required codeblocks

first make a plan on how to achieve this, review the neccessary files, then execute the implementation plan

ensure this is sensitively documented - users take responsibility for HOW code is executed, this is just a representation of it

-- YAML GUIDANCE --

Short version: use YAML **block literals** for the code, keep it as **data** (never as YAML tags/objects), and run it via a sandboxed runner you control. Avoid quoting multi-line code with `'...'` or `"..."`-that’s where most headaches come from.

Here’s a safe, tidy pattern you can adopt right now.

```yaml
witnesses:
  - name: five_step_gate
    language: python           # enum: python | node | bash | …
    entrypoint: python3        # how to run it
    timeout_ms: 5000           # execution guardrails
    env:                       # explicit, small env allowlist
      PS_REPORT: artifacts/examples/problem_solving_ok.json
    code: |-
      import json, os

      p = os.getenv("PS_REPORT", "artifacts/examples/problem_solving_ok.json")
      with open(p) as f:
          r = json.load(f)

      need = ["objective","assumptions","plan","evidence","summary"]
      missing = [k for k in need if not r.get(k)]
      assert not missing, f"Missing fields: {missing}"
      assert isinstance(r["assumptions"], list) and len(r["assumptions"]) >= 1
      assert isinstance(r["evidence"], list) and any(len(str(e)) >= 10 for e in r["evidence"])
```

Why this is better than your current single-quoted string:

* `|` (literal block) keeps newlines and characters **exactly** (no escaping hassles, no accidental folding).
* `|-` strips the final trailing newline so digests are stable; use `|+` if you deliberately want to keep it.
* Indentation is explicit; colons, hashes, and dashes inside code can’t confuse the YAML parser.

---

## Read/write considerations (practical checklist)

**YAML formatting**

* **Use UTF-8** and YAML **1.2** (JSON-compatible). Start documents with `---` if you have multiple docs.
* **Indent with spaces only** (no tabs). Two spaces is conventional.
* Prefer **block literals** for code (`|`, `|-`, `|+`). Avoid multi-line `'single'` or `"double"` quotes for code.
* If you must quote short one-liners, single quotes are safest; double quotes interpret escapes like `\n`.
* Pitfalls to avoid in *plain* scalars (unquoted): `:` followed by space, `#`, `- ` at line start-these can change meaning. Block literals avoid this entirely.

**Round-tripping (preserving style & comments)**

* Python: prefer **ruamel.yaml** if you need to read → modify → write while **preserving block styles and comments**.
  PyYAML will parse fine but won’t preserve comments or styles on emit.
* Node: use the **`yaml`** package (eemeli). It supports CST/AST and block scalar styles.

**Integrity and provenance**

* If you’ll execute these, add **integrity metadata**:

  * `sha256:` of the **normalized** code (e.g., LF line endings, no trailing whitespace) to detect tampering.
  * `source_path:` if you keep code in a file, plus its `sha256`. Example:

    ```yaml
    code_ref:
      path: checks/five_step_gate.py
      sha256: "b8a2...f3"
    ```

  Storing code in files (with a hash) is excellent for tooling, linting, and diffs; embedding is fine for portability. You can support **either** `code:` **or** `code_ref:` in your schema.

**Schema tips (make execution explicit)**
Add a few fields so your runner is deterministic and safe:

* `language` (enum), `entrypoint`, optional `args: []`, `env: {}`, optional `stdin: ""`,
* `timeout_ms`, `memory_mb`, `net: false`, `fs_mode: "ro"` (read-only), `workdir:`.

---

## Security & execution (the big one)

Treat anything under `witnesses[*].code` as **untrusted**. Safe practice:

* **Parse YAML safely**

  * Python: `yaml.safe_load` or ruamel’s safe loader; never `yaml.load` with default/FullLoader.
  * Node: `yaml.load` with default schema is safe-don’t enable custom schemas/tags you don’t need.
  * **Do not** accept or emit language-specific YAML tags like `!!python/object` etc.

* **Sandbox execution**
  Run witnesses in a locked-down environment:

  * No network (`net=none`), read-only workspace, narrow `env` allowlist, controlled `cwd`.
  * CPU, memory, and **wall-clock timeouts** (e.g., `ulimit`, cgroups, containers, Firecracker/NSJail, or similar).
  * Drop privileges (no root), use a temp user, limit file descriptors.
  * Capture **stdout/stderr/exit code** for your certificates; don’t let code decide its own pass/fail silently.

* **Determinism**
  If you stamp results, normalize inputs: line endings to LF, strip trailing spaces, fix locale, seed RNG, stable timestamps (or deny them).

---

## Writing examples (Python & JS)

**Python (ruamel.yaml) preserving `|` style**

```python
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString

yaml = YAML()
data = yaml.load(open("witnesses.yaml"))
w = data["witnesses"][0]
w["code"] = LiteralScalarString(w["code"])  # ensure literal style on write
yaml.dump(data, open("witnesses.yaml", "w"))
```

**Node (yaml) ensuring block literal on emit**

```js
const YAML = require('yaml');
const doc = YAML.parseDocument(fs.readFileSync('witnesses.yaml', 'utf8'));
const w = doc.get('witnesses').get(0);
const codeNode = new YAML.Scalar(w.get('code'));
codeNode.type = YAML.Scalar.BLOCK_LITERAL;
w.set('code', codeNode);
fs.writeFileSync('witnesses.yaml', String(doc));
```

---

## A compact schema you can adopt

```yaml
witnesses:
  - name: string
    language: python | node | bash
    entrypoint: string           # e.g., python3, node, bash
    args: []                     # optional
    env: {}                      # explicit allowlist
    workdir: "."                 # optional
    timeout_ms: 5000             # guards
    memory_mb: 128               # guards
    net: false                   # guards
    fs_mode: ro                  # ro/rw
    code: |-
      # your code here
    # or:
    # code_ref:
    #   path: checks/five_step_gate.py
    #   sha256: "…"
    # sha256: "…"               # of normalized `code` (if embedded)
```

That gives you:

* Clean YAML that humans can read and diff.
* Stable hashing for certification.
* Clear, enforceable execution boundaries.
* Zero YAML-gotchas from quoting/folding.

