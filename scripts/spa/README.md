# Truth Capsules SPA Generator

Template-based generator for the Truth Capsules System Prompt Composer web app.

## Architecture

The SPA uses a clean **template-first architecture**:

```
spa/
├── template.html      # Clean HTML template with {{ placeholders }}
├── generate_spa.py    # Data loader + Jinja2 renderer (~150 lines)
└── README.md          # This file
```

**Benefits:**
- Clean separation: HTML is HTML, Python is Python
- Template is maintainable (syntax highlighting, linting)
- Generator is simple and obvious (~150 lines vs 800+ line monolith)
- Easy to enhance without rewriting

## Usage

### Generate SPA with Latest Data

```bash
python spa/generate_spa.py \
  --root truth-capsules-v1 \
  --template spa/template.html \
  --output capsule_composer.html
```

**Output:**
```
📦 Collecting data from truth-capsules-v1...
  ✓ 24 capsules
  ✓ 6 bundles
  ✓ 7 profiles

📄 Loading template from spa/template.html...

🔧 Rendering SPA...

✅ Generated capsule_composer.html (96.7 KB)
   Generated at: 2025-11-07T15:41:36Z
   Data snapshot: 24 capsules, 6 bundles, 7 profiles
```

### Arguments

- `--root` (required): Path to `truth-capsules-v1` directory
- `--template` (optional): Path to template file (default: `spa/template.html`)
- `--output` (optional): Output HTML path (default: `capsule_composer.html`)

## How It Works

1. **Data Collection**: Scans `--root` for YAML files
   - Identifies **capsules** by `id`, `version`, `domain`
   - Identifies **bundles** by `capsules` list
   - Identifies **profiles** by `kind: profile`

2. **Template Rendering**: Uses Jinja2 to inject data
   - `{{ data_json }}` → Embedded JSON object
   - `{{ generated_at }}` → ISO timestamp

3. **Output**: Self-contained HTML with frozen data snapshot

## Snapshot vs Live Data

The generated HTML is a **snapshot viewer** with data frozen at generation time:

**Snapshot Mode (Current):**
- ✅ Works as static file (no server required)
- ✅ Easy to host (GitHub Pages, S3, etc.)
- ✅ Fast loading (no fetch requests)
- ❌ Data is stale until regenerated

**Live Mode (Future):**
- Would require a dev server (`python -m http.server`)
- Would use `fetch()` API to load YAML dynamically
- More complex for casual users

**Decision:** Snapshot mode is appropriate for v1. Users regenerate when capsules change.

## Regeneration Workflow

### When to Regenerate

Regenerate the SPA when:
- You add/modify capsules in `truth-capsules-v1/capsules/`
- You add/modify bundles in `truth-capsules-v1/bundles/`
- You add/modify profiles in `truth-capsules-v1/profiles/`
- You want to update the generation timestamp

### Quick Regeneration

```bash
# From project root
python spa/generate_spa.py --root truth-capsules-v1 --output capsule_composer.html

# Open in browser
open capsule_composer.html  # macOS
xdg-open capsule_composer.html  # Linux
start capsule_composer.html  # Windows
```

### Automated Regeneration (CI)

Add to your CI workflow:

```yaml
- name: Regenerate SPA
  run: |
    pip install jinja2 pyyaml
    python spa/generate_spa.py \
      --root truth-capsules-v1 \
      --output capsule_composer.html

- name: Upload SPA artifact
  uses: actions/upload-artifact@v3
  with:
    name: capsule-composer
    path: capsule_composer.html
```

## Template Customization

The template is standard HTML with Jinja2 placeholders.

**Available Variables:**
- `{{ data_json }}`: JSON string with capsules, bundles, profiles
- `{{ generated_at }}`: ISO timestamp (e.g., `2025-11-07T15:41:36.574005Z`)

**Example Customization:**

Edit `spa/template.html`:

```html
<div class="small">
  Generated {{ generated_at }}
  <span class="badge">v1.0.0</span>  <!-- Add version badge -->
</div>
```

Then regenerate:

```bash
python spa/generate_spa.py --root truth-capsules-v1 --output capsule_composer.html
```

## Troubleshooting

### Missing Jinja2 Dependency

```
ModuleNotFoundError: No module named 'jinja2'
```

**Fix:**
```bash
pip install jinja2
```

### Missing YAML Dependency

```
ModuleNotFoundError: No module named 'yaml'
```

**Fix:**
```bash
pip install pyyaml
```

### Template Not Found

```
ERROR: Template not found: spa/template.html
```

**Fix:** Ensure you're running from the project root, not inside `spa/` directory:

```bash
cd /path/to/truth_capsules_poc
python spa/generate_spa.py --root truth-capsules-v1 --output capsule_composer.html
```

### Data Not Updating

The SPA embeds a **snapshot** of data at generation time. To see changes:

1. Modify capsules/bundles/profiles in `truth-capsules-v1/`
2. **Regenerate** the SPA: `python spa/generate_spa.py ...`
3. Refresh browser (hard refresh: Cmd+Shift+R or Ctrl+F5)

## Future Enhancements

Post-v1 ideas based on user feedback:

- **Live Mode**: Dev server with `fetch()` API for live YAML loading
- **Provenance Panel**: Modal showing signature verification + author info
- **URL Parameters**: Share links with pre-selected bundles (e.g., `?bundle=pr_review`)
- **Export as YAML**: Save bundle selections as new bundle file
- **Validation UI**: Visual feedback on linting errors
- **Search & Tags**: Filter capsules by tags/domain/text

See [main TODO.md](../truth-capsules-v1/TODO.md) for prioritized backlog.

## Architecture Philosophy

This template-first approach follows the principle:

> **Use the right tool for the job.**
> - HTML for markup
> - Python for data wrangling
> - Jinja2 for templating

**Not over-engineered** (no React/Vue/bundlers for v1)
**Not under-engineered** (clean separation, not HTML strings in Python)
**Just right** (professional, maintainable, extensible)

This shows good technical judgment for a v1 demo while leaving room to grow.
