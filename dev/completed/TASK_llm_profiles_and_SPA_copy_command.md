This makes the SPA a “copy → paste → run” tool. Here’s a tight, idiot-proof implementation spec you can hand to an implementation LLM. I’ve kept scope small, safe, and Linux-bash-only as requested, with clear acceptance tests.

---

# Feature Spec — “Copy LLM Command” with injected System Prompt

## Goal

From the SPA, let a user select a prebuilt `llm` CLI request template, auto-inject the **currently composed system prompt**, optionally type the **user input**, and copy a **fully runnable bash command** that Just Works™.

## Footprint

1. New repo folder: `llm_templates/`
2. Update `scripts/spa/generate_spa.py` to ingest templates and embed them into the SPA JSON payload.
3. SPA UI changes: a small **“Copy LLM Cmd”** button → opens a modal → choose template → type optional input → copy command.
4. Robust prompt injection/escaping (bash-safe), no external deps.

---

## 1) Templates folder & schema

### Folder

```
llm_templates/
  openai_gpt4o_chat.yaml
  anthropic_sonnet_chat.yaml
  ollama_llama3_local.yaml
  openrouter_mixtral_chat.yaml  (optional)
  README.md
```

### Template schema (`*.yaml`)

```yaml
id: anthropic_sonnet_chat          # unique
label: "Anthropic: Claude 3.5 Sonnet (chat)"
model: "anthropic:claude-3-5-sonnet"
description: "Chat completion with system prompt; user input as arg (here-string)."
engine: "llm"                      # fixed for this repo (Simon Willison’s llm)
input_mode: "arg"                  # one of: arg | stdin | file
extra_flags: ["--no-stream"]       # optional, array of flags
# Command skeleton with placeholders (final composition happens in SPA)
# Placeholders:
#   {{SYS_HEREDOC}} → bash snippet defining $SYS using literal heredoc
#   {{USER_ARG}}    → a quoted here-string '...'
#   {{STDIN_PIPE}}  → "printf %s '...' |"
#   {{FILE_PATH}}   → a quoted path
#   {{MODEL}}       → model string (from .model)
cmd_template: |
  {{SYS_HEREDOC}}
  llm -m {{MODEL}} --system "$SYS" {{EXTRA_FLAGS}} {{INPUT_FRAGMENT}}
```

**Notes**

* We always define `$SYS` via a **literal heredoc** (robust; no escaping or line-length limits).
* `input_mode` controls how `{{INPUT_FRAGMENT}}` is formed:

  * `arg`: `<<< '{{USER_TEXT}}'` (bash here-string; requires bash)
  * `stdin`: `{{STDIN_PIPE}} llm -m ...` (pipe from `printf`)
  * `file`: `llm -m ... {{FILE_PATH}}` (argument file)

### Template examples

**`llm_templates/openai_gpt4o_chat.yaml`**

```yaml
id: openai_gpt4o_chat
label: "OpenAI: GPT-4o mini (chat)"
model: "openai:gpt-4o-mini"
description: "Chat completion; user input as arg."
engine: "llm"
input_mode: "arg"
extra_flags: []
cmd_template: |
  {{SYS_HEREDOC}}
  llm -m {{MODEL}} --system "$SYS" {{INPUT_FRAGMENT}}
```

**`llm_templates/anthropic_sonnet_chat.yaml`**

```yaml
id: anthropic_sonnet_chat
label: "Anthropic: Claude 3.5 Sonnet (chat)"
model: "anthropic:claude-3-5-sonnet"
description: "Chat completion; user input via stdin pipe."
engine: "llm"
input_mode: "stdin"
extra_flags: ["--no-stream"]
cmd_template: |
  {{SYS_HEREDOC}}
  {{STDIN_PIPE}} llm -m {{MODEL}} --system "$SYS" {{EXTRA_FLAGS}}
```

**`llm_templates/ollama_llama3_local.yaml`**

```yaml
id: ollama_llama3_local
label: "Ollama: llama3 (local)"
model: "ollama:llama3"
description: "Local model; file input."
engine: "llm"
input_mode: "file"
extra_flags: []
cmd_template: |
  {{SYS_HEREDOC}}
  llm -m {{MODEL}} --system "$SYS" {{FILE_PATH}}
```

**`llm_templates/README.md`**

* Document the placeholders and input modes.
* Mention requirement: Linux + bash + `llm` CLI installed, `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` etc.

---

## 2) SPA generator changes (`scripts/spa/generate_spa.py`)

### Load templates

* Read `llm_templates/*.yaml`, parse with `yaml.safe_load`.
* Validate minimal fields: `id,label,model,input_mode,cmd_template`.
* Embed in SPA `DATA` under `llm_templates` as a list of dicts (keep `extra_flags` too).

Pseudo-diff:

```python
def index_llm_templates(root):
    out = []
    for fp in sorted(glob.glob(os.path.join(root, "llm_templates", "*.yaml"))):
        t = load_yaml(fp)
        # validate...
        out.append({
            "id": t["id"],
            "label": t.get("label", t["id"]),
            "model": t["model"],
            "description": t.get("description", ""),
            "input_mode": t.get("input_mode", "arg"),
            "extra_flags": t.get("extra_flags", []),
            "cmd_template": t["cmd_template"],
        })
    return out

DATA = {
  "profiles": ...,
  "bundles": ...,
  "capsules": ...,
  "llm_templates": index_llm_templates(root),
  ...
}
```

No other back-end change needed.

---

## 3) SPA UI changes

### Header button

Add a button next to “Copy / Download”:

```
<button class="btn" id="copyLlmBtn">Copy LLM Cmd</button>
```

### Modal

Add a modal with:

* Template selector (radio or select)
* “Injection method”: **Heredoc (recommended)** (default; only option in v1)
* Textarea for **User input text** (optional; enabled if template `input_mode` is `arg` or `stdin`)
* Optional file path input (shown if `input_mode == 'file'`)
* Checkbox “Minify system prompt (single line)” (optional; off by default)
* “Copy” button that assembles and copies the command.

### JS helpers (SPA)

**A. Heredoc for system prompt (safe literal)**

```js
function buildSysHeredoc(promptText) {
  // Use single-quoted heredoc label to disable interpolation/globbing.
  const label = "__SYS__";
  return [
    `read -r -d '' SYS <<'${label}'`,
    promptText,   // literal
    label
  ].join("\n");
}
```

**B. Shell quoting for user input and file path**

```js
function shQuoteLiteral(s) {
  // POSIX-safe single-quote wrapper: ' becomes '\''.
  return `'` + String(s).replace(/'/g, `'\\''`) + `'`;
}
```

**C. Build input fragment from template.input_mode**

```js
function buildInputFragment(tpl, userText, filePath) {
  const flags = (tpl.extra_flags || []).join(' ');
  if (tpl.input_mode === 'arg') {
    return {
      EXTRA_FLAGS: flags,
      INPUT_FRAGMENT: `<<< ${shQuoteLiteral(userText || "")}`
    };
  }
  if (tpl.input_mode === 'stdin') {
    // Use printf to preserve trailing newlines
    return {
      EXTRA_FLAGS: flags,
      STDIN_PIPE: `printf %s ${shQuoteLiteral(userText || "")} |`,
      INPUT_FRAGMENT: ""   // not used
    };
  }
  if (tpl.input_mode === 'file') {
    return {
      EXTRA_FLAGS: flags,
      FILE_PATH: shQuoteLiteral(filePath || "input.txt"),
      INPUT_FRAGMENT: ""   // handled by FILE_PATH
    };
  }
  return { EXTRA_FLAGS: flags, INPUT_FRAGMENT: "" };
}
```

**D. Assembler**

```js
function composeLlmCommand(tpl, systemPrompt, userText, filePath, minify) {
  const sysText = minify ? systemPrompt.replace(/\s+/g, ' ').trim() : systemPrompt;
  const sysHeredoc = buildSysHeredoc(sysText);

  const frags = buildInputFragment(tpl, userText, filePath);

  let cmd = tpl.cmd_template;
  cmd = cmd.replace("{{SYS_HEREDOC}}", sysHeredoc)
           .replace("{{MODEL}}", tpl.model)
           .replace("{{EXTRA_FLAGS}}", frags.EXTRA_FLAGS || "")
           .replace("{{INPUT_FRAGMENT}}", frags.INPUT_FRAGMENT || "");

  // Optional placeholders (present only for certain templates):
  cmd = cmd.replace("{{STDIN_PIPE}}", frags.STDIN_PIPE || "")
           .replace("{{FILE_PATH}}", frags.FILE_PATH || "");

  return cmd.replace(/[ \t]+\n/g, '\n').trim() + "\n";
}
```

**E. Wire up “Copy LLM Cmd”**

* On click:

  1. Open modal.
  2. Default select first template.
  3. Pre-fill user input textarea with empty string.
  4. When user clicks **Copy**, get current system prompt from `#out` (strip ``` fences if Markdown preview is on), assemble via `composeLlmCommand(...)`, then `navigator.clipboard.writeText(cmd)`.

**F. Edge cases**

* If no capsules selected → still allow copy (system prompt may only contain profile rules).
* If Markdown preview is enabled (``` fences) — strip them before heredoc.

---

## 4) Escaping policy

* **System prompt**: injected via **literal heredoc**, so **no escaping needed**; preserves newlines & special chars; avoids shell line-length limits.
* **User input**: quoted via **POSIX single-quote** (`shQuoteLiteral`), so safe for `<<<` or `printf`.
* **File path**: also quoted via `shQuoteLiteral`.
* **Minify option**: purely optional convenience, off by default; warns that minification collapses whitespace.

---

## 5) UX details (copy modal)

Fields:

* Template (select): populated from `DATA.llm_templates[*].label`
* Description (small muted text under select)
* Input mode hints:

  * If `arg` → show textarea “Your input”
  * If `stdin` → textarea “Your input (will be piped)”
  * If `file` → input “File path” (default `input.txt`)
* [ ] Minify system prompt to one line (tooltip: “collapses whitespace; may affect formatting”)
* Buttons: **Copy**, Cancel

Success toast: “Command copied”.

---

## 6) Cheatsheet additions (docs)

Add section to `CHEATSHEET.md`:

```md
### Copy a ready-to-run `llm` command from the SPA
1. Compose a prompt in the SPA.
2. Click **Copy LLM Cmd**.
3. Pick a template (OpenAI/Anthropic/Ollama/etc).
4. (Optional) Type your input, or a file path.
5. Click **Copy**, then paste in your terminal.

> The command sets `SYS` via a literal heredoc, so it’s robust to newlines and special characters.
```

Add a 1-liner example for each template.

---

## 7) Acceptance tests

**T1 — Template loading**

* Given 3 valid YAML files in `llm_templates/`, `generate_spa.py` embeds them under `DATA.llm_templates` with all fields present.

**T2 — Heredoc output**

* When composing with a multi-line system prompt containing quotes, `$`, backticks, and emoji, copied command uses `read -r -d '' SYS <<'__SYS__'`… and preserves content bit-for-bit.

**T3 — Input modes**

* `arg`: output contains `<<< 'user text'` and runs under `/bin/bash`.
* `stdin`: output starts with `printf %s 'user text' | llm ...` and produces identical result to pasting input in terminal.
* `file`: output contains the quoted file path and runs without prompting for stdin.

**T4 — Minify toggle**

* With “minify” enabled, system prompt is 1 line (no newlines).
* With “minify” disabled, prompt retains original newlines.

**T5 — No templates**

* If no templates found, button is disabled with tooltip “No `llm_templates` found”.

**T6 — Clipboard**

* Clicking **Copy** writes the composed command to the clipboard (browser-supported).

---

## 8) Non-goals / constraints (v1)

* Linux + bash only (we rely on here-strings and heredocs).
* We don’t execute anything from the browser; we only copy text.
* No base64 fiddling (heredoc is simpler and universally available).
* No API key management in SPA.

---

## 9) Value assessment

**Why this moves the needle:**

* Eliminates friction from “compose → save prompt → craft command → escape newlines”.
* Reduces support load: fewer user mistakes with quoting/escaping.
* Encourages adoption: one-click **ready-to-run** commands for OpenAI/Anthropic/Ollama.
* Cleanly extensible: just drop a new YAML template in `llm_templates/` to surface new providers/models.

**Risk/complexity:**

* Low technical risk; small JS and Python changes; clear acceptance tests.
* Heredoc approach avoids the hardest class of escaping bugs.

---

## 10) Tiny implementation checklist

* [ ] Create `llm_templates/` with 2–3 starter YAMLs.
* [ ] Update `scripts/spa/generate_spa.py` to embed templates in `DATA.llm_templates`.
* [ ] Add “Copy LLM Cmd” button and modal (HTML/CSS/JS) to `scripts/spa/template.html`.
* [ ] Implement `shQuoteLiteral`, `buildSysHeredoc`, `composeLlmCommand`.
* [ ] Strip ``` fences when copying if Markdown preview is on.
* [ ] Add docs to `CHEATSHEET.md` + `llm_templates/README.md`.
* [ ] Run acceptance tests T1–T6.

---

### Example of final copied command (Anthropic / stdin mode)

```bash
read -r -d '' SYS <<'__SYS__'
SYSTEM: Profile=Conversational Guidance
POLICY: Cite or abstain; follow Plan→Verify→Answer; ask ONE crisp follow-up if required.
...
__SYS__
printf %s 'Summarize the attached doc and list 3 risks.' | llm -m anthropic:claude-3-5-sonnet --system "$SYS" --no-stream
```

and for OpenAI / arg mode:

```bash
read -r -d '' SYS <<'__SYS__'
SYSTEM: ...
__SYS__
llm -m openai:gpt-4o-mini --system "$SYS" <<< 'Perform capsule-compliant PR review. Highlight risky changes and propose tests.'
```

---

If you want, we can add a **“Save as script”** checkbox that wraps the command in a tiny `.sh` with `#!/usr/bin/env bash`—but I’d keep that for v1.1.
