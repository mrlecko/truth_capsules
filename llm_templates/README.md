# LLM Command Templates

This directory contains YAML templates for generating ready-to-run `llm` CLI commands with injected system prompts from the Truth Capsules SPA.

## Requirements

- **Linux + bash** (relies on here-strings `<<<` and heredocs)
- **llm CLI** installed (`pip install llm`)
- **API Keys** configured as environment variables:
  - `OPENAI_API_KEY` for OpenAI models
  - `ANTHROPIC_API_KEY` for Anthropic models
  - Ollama requires local installation (`ollama pull llama3`)

## Template Schema

Each YAML template defines:

- **id**: Unique identifier
- **label**: Human-readable name shown in SPA
- **model**: Model identifier for `llm -m` flag
- **description**: Brief explanation
- **engine**: Always `"llm"` (Simon Willison's llm CLI)
- **input_mode**: How user input is provided:
  - `arg`: Bash here-string `<<< 'text'`
  - `stdin`: Piped via `printf %s 'text' |`
  - `file`: File path argument
- **extra_flags**: Optional array of additional flags
- **cmd_template**: Command skeleton with placeholders

## Placeholders

Templates use these placeholders for dynamic substitution:

- `{{SYS_HEREDOC}}` → Bash heredoc defining `$TC_SYSTEM` variable (safe for newlines/quotes)
- `{{MODEL}}` → Model identifier from template
- `{{EXTRA_FLAGS}}` → Space-separated flags
- `{{INPUT_FRAGMENT}}` → Varies by input_mode:
  - `arg`: `<<< 'user text'`
  - `stdin`: `printf %s 'user text' |` (appears before llm command)
  - `file`: Path to input file
- `{{STDIN_PIPE}}` → Only for stdin mode (pipe prefix)
- `{{FILE_PATH}}` → Only for file mode (quoted path)

**Note:** The variable `TC_SYSTEM` (Truth Capsules SYSTEM) is used instead of `SYS` to avoid conflicts with users' existing shell variables.

## Safety

- **System prompts** use literal heredocs (no escaping needed)
- **User input** uses POSIX single-quote escaping (`'` becomes `'\''`)
- **No shell injection** possible with proper quoting

## Adding New Templates

1. Create `new_template.yaml` with required fields
2. Choose appropriate `input_mode` for your use case
3. Test the generated command manually
4. Regenerate SPA: `python scripts/spa/generate_spa.py --root . --output capsule_composer.html`

## Examples

### OpenAI (arg mode)
```bash
read -r -d '' TC_SYSTEM <<'__TC_SYSTEM__'
You are a helpful assistant. Always cite sources.
__TC_SYSTEM__
llm -m gpt-4o-mini --system "$TC_SYSTEM" <<< 'Explain quantum computing'
```

### Anthropic (stdin mode)
```bash
read -r -d '' TC_SYSTEM <<'__TC_SYSTEM__'
You are a code reviewer. Be thorough and constructive.
__TC_SYSTEM__
printf %s 'Review this PR for security issues' | llm -m anthropic:claude-3-5-sonnet --system "$TC_SYSTEM" --no-stream
```

### Ollama (file mode)
```bash
read -r -d '' TC_SYSTEM <<'__TC_SYSTEM__'
Summarize the document concisely.
__TC_SYSTEM__
llm -m ollama:llama3 --system "$TC_SYSTEM" /path/to/document.txt
```

## Notes

- Commands are Linux/bash specific (not Windows compatible)
- The SPA generates these commands client-side (no server execution)
- Minification option collapses whitespace but preserves semantics
- All special characters in prompts are preserved via heredoc
