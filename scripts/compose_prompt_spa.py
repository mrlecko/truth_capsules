#!/usr/bin/env python3
import argparse, json, os, sys, glob, yaml, html, datetime

def slurp(path, default=""):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return default

def read_yaml(fp):
    try:
        with open(fp, "r", encoding="utf-8") as f:
            raw = f.read()
        data = yaml.safe_load(raw)
        if isinstance(data, dict):
            data['__raw__'] = raw
        return data
    except Exception as e:
        return {"__error__": str(e), "__file__": fp}

def collect(input_dir):
    capsules, bundles, profiles, schemas = {}, {}, {}, {}
    # YAML files
    files = glob.glob(os.path.join(input_dir, "**", "*.yml"), recursive=True) + \
            glob.glob(os.path.join(input_dir, "**", "*.yaml"), recursive=True)
    for fp in files:
        y = read_yaml(fp)
        if not isinstance(y, dict):
            continue
        # profiles
        if (y.get("kind") == "profile") and y.get("id"):
            pid = y["id"]
            profiles[pid] = {
                "id": pid,
                "title": y.get("title", pid),
                "version": y.get("version","0.0.0"),
                "description": y.get("description",""),
                "response": y.get("response", {}),
                "download": y.get("download", {"suggested_ext":"txt"}),
                "__file__": fp
            }
            continue
        # bundles
        if "capsules" in y and isinstance(y.get("capsules"), list) and ("id" not in y or "witnesses" not in y):
            name = y.get("name") or os.path.basename(fp)
            bundles[name] = {
                "name": name,
                "applies_to": y.get("applies_to", []),
                "capsules": y.get("capsules", []),
                "modes": y.get("modes", []),
                "env": y.get("env", {}),
                "secrets": y.get("secrets", []),
                "__file__": fp
            }
            continue
        # capsules
        if "id" in y and "witnesses" in y:
            cap_id = y.get("id")
            ped = y.get("pedagogy", [])
            pedos = []
            for p in ped or []:
                if isinstance(p, dict):
                    pedos.append({"kind": p.get("kind","Note"), "text": p.get("text","")})
                elif isinstance(p, str):
                    pedos.append({"kind": "Note", "text": p})
            capsules[cap_id] = {
                "id": cap_id,
                "version": y.get("version","0.0.0"),
                "domain": y.get("domain",""),
                "title": y.get("title",""),
                "statement": (y.get("statement","") or "").strip(),
                "assumptions": y.get("assumptions", []),
                "pedagogy": pedos,
                "tags": y.get("tags", []),
                "__file__": fp,
                "__raw__": y.get("__raw__","")
            }
    # Schemas (JSON)
    for fp in glob.glob(os.path.join(input_dir, "schemas", "*.json")):
        try:
            schemas[os.path.basename(fp)] = json.load(open(fp, "r", encoding="utf-8"))
        except Exception as e:
            schemas[os.path.basename(fp)] = {"__error__": str(e), "__file__": fp}
    return capsules, bundles, profiles, schemas

DEFAULT_LOADER = """SYSTEM: Truth Capsules Loader v1
PURPOSE: Use curated capsules to scaffold reasoning and enforce acceptance rules.
METHOD:
  1) Load capsule rules (below).
  2) For each task, follow Plan → Verify → Answer.
  3) If required fields are missing, ask ONE concise follow-up.
  4) Cite sources or abstain. Redact PII. Validate tool JSON before calling.
  5) Emit a JSON report when asked (see REPORT_SCHEMA).
FAILURE POLICY: If a capsule cannot be satisfied, abstain + explain what is missing.
"""

DEFAULT_BOOTSTRAP = """SYSTEM: Bootstrap Discipline
• Curation is king - prefer curated fixtures/evidence; abstain when unsure.
• Show your work - reference evidence in answers.
• Make failures explicit and reversible - choose tiny experiments.
"""

HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>__TITLE__</title>
<style>
  :root { --bg:#0b0f14; --fg:#e6edf3; --muted:#93a1ad; --card:#11161d; --accent:#4cc38a; --warn:#ffb86c; }
  html, body { margin:0; font-family: ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Inter,Arial; background:var(--bg); color:var(--fg); }
  header { padding:20px; border-bottom:1px solid #202938; background:#0e141b; position:sticky; top:0; z-index:2; }
  h1 { margin:0; font-size:20px; }
  .wrap { display:grid; grid-template-columns: 340px 1fr; gap:16px; padding:16px; }
  .panel { background:var(--card); border:1px solid #202938; border-radius:12px; padding:14px; }
  .sec-title { font-size:12px; text-transform:uppercase; letter-spacing:0.12em; color:var(--muted); margin:0 0 8px; }
  .list { max-height: 50vh; overflow-y:auto; overflow-x:hidden; border-top:1px solid #1b2230; }
  .item { display:flex; gap:8px; align-items:flex-start; padding:10px 0; border-bottom:1px dashed #1b2230; }
  .item input { margin-top:3px; }
  .muted { color: var(--muted); font-size:12px; }
  .pill { display:inline-block; padding:2px 6px; border:1px solid #2a3244; border-radius:999px; margin-right:6px; font-size:11px; color:#b8c3cf; }
  .btn { background:var(--accent); color:#082b1a; border:none; padding:10px 14px; border-radius:10px; font-weight:600; cursor:pointer; }
  .btn:disabled { opacity:.5; cursor:not-allowed; }
  .toolbar { display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin-top:8px; }
  textarea { width:100%; height:55vh; background:#0c1218; color:#e6edf3; border:1px solid #202938; border-radius:12px; padding:12px; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; white-space: pre; }
  input[type="search"] { width:100%; padding:8px 10px; border-radius:10px; background:#0c1218; color:#e6edf3; border:1px solid #202938; }
  small.file { display:block; color:#6f7b89; margin-top:4px; word-break: break-all; }
  footer { padding:16px; text-align:center; color:#6f7b89; }
  .lint { margin-top: 8px; padding:8px; background:#0c1218; border:1px solid #202938; border-radius:8px; }
  .lint strong { color:#ffb86c; }
  .handle { cursor:grab; margin-right:8px; user-select:none; }
  .modal{ position:fixed; inset:0; background:rgba(0,0,0,.6); display:none; align-items:center; justify-content:center; z-index:10; }
  .badge{ display:inline-block; padding:2px 6px; border-radius:999px; font-size:10px; margin-left:6px; }
  .badge.ok{ background:#153a2b; color:#63d3a7; border:1px solid #1f6b52; }
  .badge.warn{ background:#3a2e15; color:#ffcc85; border:1px solid #6b501f; }
  .modal.show{ display:flex; }
  .modal-card{ width:min(900px,90vw); max-height:80vh; overflow:auto; background:#0c1218; border:1px solid #202938; border-radius:12px; box-shadow:0 10px 40px rgba(0,0,0,.5); }
  .modal-header{ display:flex; align-items:center; justify-content:space-between; padding:10px 14px; border-bottom:1px solid #202938; }
  .modal-header h3{ margin:0; font-size:14px; color:#b8c3cf; }
  .modal-body{ padding:12px; }
  .modal-body pre{ margin:0; white-space:pre; color:#d4dfeb; }
  .icon-btn{ background:transparent; border:1px solid #2a3244; color:#b8c3cf; padding:4px 8px; border-radius:8px; cursor:pointer; font-size:12px; }
</style>
</head>
<body>
<header>
  <h1>Truth Capsule System Prompt Composer</h1>
  <div class="muted">Generated __STAMP__ UTC</div>
</header>
<div class="wrap">
  <aside class="panel">
    <div>
      <div class="sec-title">Search</div>
      <input id="q" type="search" placeholder="Filter by id/title/domain/statement…"/>
    </div>

    <div style="margin-top:12px">
      <div class="sec-title">Profiles</div>
      <div>
        <select id="profile"></select>
        <div id="profileDesc" class="muted" style="margin-top:6px"></div>
      </div>
    </div>

    <div style="margin-top:12px">
      <div class="sec-title">Bundles</div>
      <div id="bundles" class="list"></div>
    </div>

    <div style="margin-top:12px">
      <div class="sec-title">Capsules</div>
      <div id="capsules" class="list"></div>
    </div>
  </aside>

  <main class="panel">
    <div class="sec-title">Composed SYSTEM Prompt</div>
    <div class="toolbar">
      <button class="btn" id="composeBtn">Compose</button>
      <button class="btn" id="copyBtn">Copy</button>
      <button class="btn" id="downloadBtn">Download</button>
      <button class="btn" id="downloadJsonBtn">Download JSON</button>
      <button class="btn" id="shareBtn">Share Link</button>
      <label class="muted">Format:
        <select id="format">
          <option value="text">Plain text</option>
          <option value="md">Markdown</option>
        </select>
      </label>
      <label class="muted">Mode:
        <select id="mode">
          <option value="verbose">Verbose</option>
          <option value="compact">Compact</option>
        </select>
      </label>
      <label class="muted"><input type="checkbox" id="incAssumptions" checked> Assumptions</label>
      <label class="muted"><input type="checkbox" id="incSocratic" checked> Socratic</label>
      <label class="muted"><input type="checkbox" id="incAphorisms" checked> Aphorisms</label>
      <label class="muted"><input type="checkbox" id="debugToggle"> Debug log</label>
      <span id="status" class="muted"></span>
    </div>
    <div id="debug" style="display:none; margin-top:8px; padding:8px; background:#0c1218; border:1px solid #202938; border-radius:8px; font-size:12px; height:120px; overflow:auto;"></div>
    <textarea id="output" placeholder="Click Compose to generate the prompt…"></textarea>

    <div style="margin-top:12px">
      <div class="sec-title">Preview - Selected Capsules (drag to reorder)</div>
      <div id="preview" class="list"></div>
      <div id="lint" class="lint" style="display:none"></div>
    </div>
  </main>
</div>
<footer>Truth Capsules - Executable Curation</footer>

<div id="modal" class="modal"><div class="modal-card"><div class="modal-header"><h3 id="modalTitle"></h3><div style="display:flex; gap:8px; align-items:center"><button id="modalCopy" class="icon-btn">Copy</button><button id="modalClose" class="icon-btn">Close</button></div></div><div class="modal-body"><pre id="modalBody"></pre></div></div></div>

<script>

// --- Debug helpers ---
const elDebug = document.getElementById('debug');
const elDebugToggle = document.getElementById('debugToggle');
function debugLog(...args){
  try { console.log(...args); } catch {}
  if (!elDebug) return;
  const on = elDebugToggle && elDebugToggle.checked;
  if (!on) return;
  const line = document.createElement('div');
  line.textContent = new Date().toISOString() + " | " + args.map(a => (typeof a==='object'? JSON.stringify(a): String(a))).join(" ");
  elDebug.appendChild(line);
  elDebug.scrollTop = elDebug.scrollHeight;
}
if (elDebugToggle){
  elDebugToggle.addEventListener('change', ()=>{
    elDebug.style.display = elDebugToggle.checked ? '' : 'none';
  });
}

// --- State persistence & URL share ---
const LSKEY = "truth_capsules_state_v2";

function parseQS(){
  const p = new URLSearchParams(location.search);
  const caps = (p.get('caps')||'').split(',').filter(Boolean);
  const bundles = (p.get('bundles')||'').split(',').filter(Boolean);
  const fmt = p.get('fmt')||'text';
  const mode = p.get('mode')||'verbose';
  const ass = p.get('ass')!== '0';
  const soc = p.get('soc')!== '0';
  const aph = p.get('aph')!== '0';
  const prof = p.get('prof') || '';
  return {caps, bundles, fmt, mode, ass, soc, aph, prof};
}

function saveState(state){
  try { localStorage.setItem(LSKEY, JSON.stringify(state)); } catch {}
}

function loadState(){
  const qs = parseQS();
  if (qs.caps.length || qs.bundles.length || qs.prof){
    return {
      order: qs.caps,
      selectedCaps: new Set(qs.caps),
      selectedBundles: new Set(qs.bundles),
      fmt: qs.fmt, mode: qs.mode,
      ass: qs.ass, soc: qs.soc, aph: qs.aph,
      profile: qs.prof
    };
  }
  try {
    const raw = localStorage.getItem(LSKEY);
    if (!raw) throw 0;
    const s = JSON.parse(raw);
    s.selectedCaps = new Set(s.selectedCaps||[]);
    s.selectedBundles = new Set(s.selectedBundles||[]);
    s.order = Array.isArray(s.order)? s.order : [];
    s.fmt = s.fmt || 'text'; s.mode = s.mode || 'verbose';
    s.ass = s.ass!==false; s.soc = s.soc!==false; s.aph = s.aph!==false;
    s.profile = s.profile || '';
    return s;
  } catch { 
    return {order:[], selectedCaps:new Set(), selectedBundles:new Set(), fmt:'text', mode:'verbose', ass:true, soc:true, aph:true, profile:''};
  }
}

// --- Data & defaults ---
const DATA = __DATA__;
const DEFAULT_LOADER = __LOADER__;
const DEFAULT_BOOTSTRAP = __BOOT__;

const elBundles = document.getElementById('bundles');
const elCaps = document.getElementById('capsules');
const elOut = document.getElementById('output');
const elStatus = document.getElementById('status');
const elQ = document.getElementById('q');
const elPreview = document.getElementById('preview');
// Fallback container listeners for logging
elPreview.addEventListener('dragover', (e)=>{ e.preventDefault(); debugLog('preview:dragover'); });
elPreview.addEventListener('drop', (e)=>{ e.preventDefault(); debugLog('preview:drop-container'); });
const elLint = document.getElementById('lint');
const elProf = document.getElementById('profile');
const elProfDesc = document.getElementById('profileDesc');

let STATE = loadState();

// --- Helpers ---

function badgeForCapsule(c){
  // Valid if it has id + statement + parsed YAML (__raw__ present)
  const ok = !!(c && c.id && (c.statement||'').trim() && (c.__raw__||'').length);
  const b = h('span', {class: 'badge ' + (ok ? 'ok' : 'warn')}, ok ? 'valid' : 'check');
  return b;
}


// --- Modal helpers ---
const elModal = document.getElementById('modal');
const elModalTitle = document.getElementById('modalTitle');
const elModalBody = document.getElementById('modalBody');
const elModalClose = document.getElementById('modalClose');
const elModalCopy = document.getElementById('modalCopy');
function openModal(title, bodyText){
  try { elModalTitle.textContent = title || ''; } catch {}
  try { elModalBody.textContent = bodyText || ''; } catch {}
  elModal.classList.add('show');
}
function closeModal(){ elModal.classList.remove('show'); }
elModalClose.addEventListener('click', closeModal);
elModalCopy.addEventListener('click', ()=>{ try{ navigator.clipboard.writeText(elModalBody.textContent||''); elModalCopy.textContent='Copied'; setTimeout(()=> elModalCopy.textContent='Copy', 1200);}catch(e){console.log(e);} });
elModal.addEventListener('click', (e)=>{ if(e.target===elModal) closeModal(); });

// --- Manual selection tracking ---
STATE.manualCaps = new Set((STATE.manualCaps && Array.isArray(STATE.manualCaps)) ? STATE.manualCaps : []);
function persistState(){
  saveState({ 
    ...STATE,
    selectedCaps:[...STATE.selectedCaps],
    selectedBundles:[...STATE.selectedBundles],
    manualCaps:[...STATE.manualCaps],
    order: STATE.order
  });
}

function h(tag, attrs={}, ...kids){
  const el = document.createElement(tag);
  for(const [k,v] of Object.entries(attrs||{})){
    if(k==='class') el.className = v;
    else if(k==='html') el.innerHTML = v;
    else if(k==='text') el.textContent = v;
    else el.setAttribute(k,v);
  }
  for(const kid of kids){
    if(kid==null) continue;
    if(typeof kid === 'string') el.appendChild(document.createTextNode(kid));
    else el.appendChild(kid);
  }
  return el;
}

function setToolbarFromState(){
  (document.getElementById('format')||{}).value = STATE.fmt;
  (document.getElementById('mode')||{}).value = STATE.mode;
  (document.getElementById('incAssumptions')||{}).checked = STATE.ass;
  (document.getElementById('incSocratic')||{}).checked = STATE.soc;
  (document.getElementById('incAphorisms')||{}).checked = STATE.aph;
  if (!STATE.profile){
    // default to first available profile
    const keys = Object.keys(DATA.profiles||{}).sort();
    STATE.profile = keys[0] || '';
  }
  elProf.value = STATE.profile;
  updateProfileDesc();
}

function updateProfileDesc(){
  const p = DATA.profiles[STATE.profile] || null;
  if (!p){ elProfDesc.textContent = "No profile selected."; return; }
  elProfDesc.textContent = p.description || "";
}

function collectSelections(){
  const caps = [];
  STATE.order.forEach(id => { if(STATE.selectedCaps.has(id) && DATA.capsules[id]) caps.push(DATA.capsules[id]); });
  Object.keys(DATA.capsules).sort().forEach(id => {
    if (STATE.selectedCaps.has(id) && !STATE.order.includes(id)) caps.push(DATA.capsules[id]);
  });
  return caps;
}

function lintCaps(caps){
  const warns = [];
  const seen = new Set();
  caps.forEach(c=>{
    if(!c.statement || !c.statement.trim()) warns.push(`Capsule ${c.id} has no statement.`);
    if(seen.has(c.id)) warns.push(`Duplicate capsule id in selection: ${c.id}`);
    seen.add(c.id);
  });
  // Simple profile-format compatibility hints
  const prof = DATA.profiles[STATE.profile];
  if (prof && prof.response && prof.response.format === 'json' && (document.getElementById('format')||{}).value === 'md'){
    warns.push("Profile expects JSON output; you're composing Markdown for the prompt (that is fine, but downstream expects JSON from the model).");
  }
  return warns;
}

// --- Render lists ---
function render(){
  // profiles dropdown
  elProf.innerHTML = '';
  Object.values(DATA.profiles).sort((a,b)=>a.title.localeCompare(b.title)).forEach(p=>{
    elProf.appendChild(h('option', {value:p.id, text:`${p.title} (${p.version})`}));
  });

  setToolbarFromState();

  const q = (elQ.value||'').toLowerCase();
  elBundles.innerHTML='';
  Object.values(DATA.bundles).sort((a,b)=>a.name.localeCompare(b.name)).forEach(b=>{
    const text = [b.name, (b.applies_to||[]).join(','), (b.capsules||[]).join(',')].join(' ').toLowerCase();
    if(q && !text.includes(q)) return;
    const id = 'bundle_'+b.name;
    const cb = h('input',{type:'checkbox', id});
    cb.checked = STATE.selectedBundles.has(b.name);
    cb.addEventListener('change', ()=> {
      if(cb.checked) { 
        STATE.selectedBundles.add(b.name);
        (b.capsules||[]).forEach(cid=> { 
          STATE.selectedCaps.add(cid); 
          if(!STATE.order.includes(cid)) STATE.order.push(cid);
        }); 
      } else { 
        STATE.selectedBundles.delete(b.name);
        const others = [...STATE.selectedBundles];
        (b.capsules||[]).forEach(cid=> { 
          const includedElsewhere = others.some(name => (DATA.bundles[name]||{}).capsules && (DATA.bundles[name].capsules||[]).includes(cid));
          const manuallyKept = STATE.manualCaps.has(cid);
          if(!includedElsewhere && !manuallyKept){ STATE.selectedCaps.delete(cid); }
        });
      }
      persistState();
      syncPreview();
    });
    elBundles.appendChild(h('div',{class:'item'},
      cb,
      h('label', {for:id}, h('div',{}, b.name), h('div',{class:'muted'}, (b.applies_to||[]).join(', ')||'bundle'), h('small',{class:'file'}, b.__file__||''))
    ));
  });

  elCaps.innerHTML='';
  Object.values(DATA.capsules).sort((a,b)=>a.id.localeCompare(b.id)).forEach(c=>{
    const text = [c.id, c.title||'', c.domain||'', c.statement||''].join(' ').toLowerCase();
    if(q && !text.includes(q)) return;
    const id = 'cap_'+c.id;
    const cb = h('input',{type:'checkbox', id});
    cb.checked = STATE.selectedCaps.has(c.id);
    cb.addEventListener('change', ()=> {
      if(cb.checked){
        STATE.selectedCaps.add(c.id);
        STATE.manualCaps.add(c.id);
        if(!STATE.order.includes(c.id)) STATE.order.push(c.id);
      } else {
        STATE.selectedCaps.delete(c.id);
        STATE.manualCaps.delete(c.id);
      }
      persistState();
      syncPreview();
    });
    const viewBtn = h('button',{class:'icon-btn', title:'View YAML'}, 'View');
    viewBtn.addEventListener('click', (e)=>{ e.stopPropagation(); e.preventDefault(); openModal(c.id, (c.__raw__||JSON.stringify(c,null,2))); });
    elCaps.appendChild(h('div',{class:'item'},
      cb,
      h('label', {for:id},
        h('div',{}, c.id, ' ', c.version?('('+c.version+')'):'', c.domain?(' - '+c.domain):'', ' ', badgeForCapsule(c)),
        h('div',{class:'muted'}, (c.title || (c.statement ? c.statement.slice(0,140) : ''))),
        h('small',{class:'file'}, c.__file__||'')
      ),
      viewBtn
    ));
  });
  syncPreview();
}

// --- Drag & drop reorder ---
let dragId = null;

function makeDraggableRow(c, idx){
  const row = h('div', {class:'item', draggable:'true', 'data-id': c.id});
  row.addEventListener('dragstart', (e)=> { 
    debugLog('dragstart', c.id);
    dragId = c.id; row.style.opacity='0.5'; 
    if (e.dataTransfer) { e.dataTransfer.setData('text/plain', c.id); e.dataTransfer.effectAllowed='move'; }
  });
  row.addEventListener('dragend', ()=> { debugLog('dragend', dragId); dragId = null; row.style.opacity=''; row.classList.remove('over'); });
  row.addEventListener('dragenter', (e)=> { e.preventDefault(); row.classList.add('over'); });
  row.addEventListener('dragleave', (e)=> { row.classList.remove('over'); });
  row.addEventListener('dragover', (e)=> { e.preventDefault(); if (e.dataTransfer) e.dataTransfer.dropEffect='move'; });
  row.addEventListener('drop', (e)=>{
    e.preventDefault();
    const target = e.currentTarget;
    target.classList.remove('over');
    const tgtId = target.getAttribute('data-id');
    // Use DOM order of preview items as current ordering baseline
    const old = Array.from(elPreview.querySelectorAll('.item')).map(n => n.getAttribute('data-id'));
    const from = old.indexOf(dragId);
    const to = old.indexOf(tgtId);
    debugLog('drop', {dragId, tgtId, from, to, old});
    if (from>=0 && to>=0 && from!==to){
      const newOrder = old.slice();
      const [moved] = newOrder.splice(from,1);
      newOrder.splice(to,0,moved);
      const rest = STATE.order.filter(id => !old.includes(id));
      STATE.order = newOrder.concat(rest);
      debugLog('reordered', {newOrder, rest});
      saveState({ ...STATE, order: STATE.order });
      syncPreview();
    } else {
      debugLog('drop-noop', {reason:'indexes', from, to});
    }
  });
  return row;
}


// --- Preview & lint ---
function syncPreview(){
  const caps = collectSelections();
// Seed STATE.order if none of the selected IDs are present
const selIds = caps.map(c=>c.id);
const present = STATE.order.filter(id => STATE.selectedCaps.has(id));
if (present.length === 0 && selIds.length > 0){
  STATE.order = selIds.slice();
  saveState({ ...STATE, order: STATE.order });
  debugLog('seed-order', {order: STATE.order});
}
  elPreview.innerHTML='';
  caps.forEach((c, idx)=>{
    const pedo = (c.pedagogy||[]).slice(0,3).map(p => h('span',{class:'pill'}, (p.kind||'Note')));
    const row = makeDraggableRow(c, idx);
    row.appendChild(h('div',{class:'handle'}, "≡"));
    row.appendChild(h('div',{class:'muted'},"●"));
    row.appendChild(h('div',{}, 
      h('div',{}, c.id, c.domain?(' - '+c.domain):'', ' ', badgeForCapsule(c)),
      h('div',{class:'muted'}, c.statement || ''),
      h('div',{}, ...pedo)
    ));
    const viewBtn2 = h('button',{class:'icon-btn', title:'View YAML'}, 'View');
    viewBtn2.addEventListener('click', (e)=>{ e.stopPropagation(); e.preventDefault(); openModal(c.id, (c.__raw__||JSON.stringify(c,null,2))); });
    row.appendChild(viewBtn2);
    elPreview.appendChild(row);
  });
  const warns = lintCaps(caps);
  if (warns.length){
    elLint.style.display = '';
    elLint.innerHTML = "<strong>Warnings:</strong><br/>" + warns.map(w=>"- "+w).join("<br/>");
  } else {
    elLint.style.display = 'none';
    elLint.innerHTML = "";
  }
  elStatus.textContent = caps.length ? `${caps.length} capsule(s) selected` : 'No capsules selected';
}

// --- Composer ---
function composePrompt(){
  const caps = collectSelections();
  const lines = [];
  const fmt = (document.getElementById('format')||{}).value || 'text';
  const mode = (document.getElementById('mode')||{}).value || 'verbose';
  const incAssumptions = (document.getElementById('incAssumptions')||{}).checked !== false;
  const incSocratic = (document.getElementById('incSocratic')||{}).checked !== false;
  const incAphorisms = (document.getElementById('incAphorisms')||{}).checked !== false;
  const prof = DATA.profiles[STATE.profile] || null;
  STATE.fmt = fmt; STATE.mode = mode; STATE.ass = incAssumptions; STATE.soc = incSocratic; STATE.aph = incAphorisms;
  saveState({ ...STATE, selectedCaps:[...STATE.selectedCaps] });

  function pushSchemaMD(ref){
    if (!ref) return;
    const key = ref.endsWith(".json") ? ref : (ref + ".json");
    const sch = DATA.schemas[key];
    if (!sch) return;
    lines.push("### " + (sch.title || "Schema"), "```json", JSON.stringify(sch, null, 2), "```");
  }
  function pushSchemaTXT(ref){
    if (!ref) return;
    const key = ref.endsWith(".json") ? ref : (ref + ".json");
    const sch = DATA.schemas[key];
    if (!sch) return;
    lines.push("SCHEMA:", JSON.stringify(sch, null, 2));
  }

  if (fmt === 'md'){
    // Markdown
    lines.push("# Truth Capsules Loader v1","");
    if (prof){
      lines.push("## Profile");
      lines.push(`**${prof.title}** (${prof.version}) - ${prof.description}`);
      if (prof.response && prof.response.system_block){
        lines.push("```", prof.response.system_block.trim(), "```");
      }
    }
    lines.push("## Purpose","Use curated capsules to scaffold reasoning and enforce acceptance rules.","");
    lines.push("## Method","1) Load capsule rules (below).","2) For each task, follow **Plan → Verify → Answer**.","3) If required fields are missing, ask **ONE** concise follow-up.","4) Cite sources or abstain. Redact PII. Validate tool JSON before calling.","5) Emit a JSON report when asked (see **Report Schema**).","");
    lines.push("## Failure Policy","If a capsule cannot be satisfied, **abstain** and explain what is missing.","");
    lines.push("## Bootstrap Discipline");
    DEFAULT_BOOTSTRAP.trim().split('\n').forEach(L => lines.push(L.replace(/^\u2022\s?/, '- ')));
    lines.push("");
    if (mode==='compact'){
      lines.push("## Capsule Rules (Compact)");
      if(!caps.length){ lines.push("- (No capsules selected)"); }
      else { caps.forEach(c=> lines.push(`- **${c.id}** - ${c.statement||c.title||''}`)); }
    } else {
      lines.push("## Capsule Rules (Selected)");
      if(!caps.length){ lines.push("- (No capsules selected)"); }
      else {
        caps.forEach(c=>{
          lines.push(`### Capsule: ${c.id} (${c.version||"?"}, ${c.domain||"-"})`);
          if (c.title) lines.push(`**Title:** ${c.title}`);
          if (c.statement) lines.push(`**Statement:** ${c.statement}`);
          if (incAssumptions && c.assumptions && c.assumptions.length){ lines.push("**Assumptions:**"); c.assumptions.slice(0,5).forEach(a=> lines.push(`- ${a}`)); }
          const soc = incSocratic ? (c.pedagogy||[]).filter(p=> (p.kind||"").toLowerCase()==="socratic") : [];
          const aph = incAphorisms ? (c.pedagogy||[]).filter(p=> (p.kind||"").toLowerCase()==="aphorism") : [];
          if (soc.length){ lines.push("**Socratic prompts:**"); soc.slice(0,5).forEach(p => lines.push(`- ${p.text}`)); }
          if (aph.length){ lines.push("**Aphorisms:**"); aph.slice(0,5).forEach(p => lines.push(`- ${p.text}`)); }
          lines.push("_Enforcement:_ Ensure outputs satisfy this capsule; otherwise abstain and request the minimal missing info.","");
        });
      }
    }
    if (prof && prof.response && prof.response.schema_ref){
      lines.push("## Attached Schema");
      pushSchemaMD(prof.response.schema_ref);
    }
  } else {
    // Plain text
    if (prof){
  lines.push(`SYSTEM: Profile=${prof.title} (id=${prof.id}, v=${prof.version})`);
  if (prof.response && prof.response.policy) lines.push(`POLICY: ${prof.response.policy.trim()}`);
  if (prof.response && prof.response.format) lines.push(`FORMAT: ${prof.response.format}`);
  lines.push("");
  if (prof.response && prof.response.system_block) lines.push(prof.response.system_block.trim(), "");
}
    DEFAULT_LOADER.trim().split('\n').forEach(L => lines.push(L)); lines.push('');
    DEFAULT_BOOTSTRAP.trim().split('\n').forEach(L => lines.push(L)); lines.push('');
    if (mode==='compact'){
      lines.push("SYSTEM: Capsule Rules (Compact)");
      if(!caps.length){ lines.push("- (No capsules selected)"); }
      else { caps.forEach(c=> lines.push(`- [${c.id}] ${c.statement || c.title || ''}`)); }
    } else {
      lines.push("SYSTEM: Capsule Rules (Selected)");
      if(!caps.length){ lines.push("- (No capsules selected)"); }
      else {
        for (const c of caps){
  lines.push(`BEGIN CAPSULE id=${c.id} version=${c.version||"?"} domain=${c.domain||"-"}`);
  if (c.title) lines.push(`TITLE: ${c.title}`);
  if (c.statement) lines.push(`STATEMENT: ${c.statement}`);
  if (incAssumptions && c.assumptions && c.assumptions.length){
    lines.push("ASSUMPTIONS:");
    c.assumptions.slice(0,5).forEach(a=> lines.push(`  - ${a}`));
  }
  const soc = incSocratic ? (c.pedagogy||[]).filter(p=> (p.kind||"").toLowerCase()==="socratic") : [];
  const aph = incAphorisms ? (c.pedagogy||[]).filter(p=> (p.kind||"").toLowerCase()==="aphorism") : [];
  if (soc.length){ lines.push("SOCRATIC:"); soc.slice(0,5).forEach(p => lines.push(`  - ${p.text}`)); }
  if (aph.length){ lines.push("APHORISMS:"); aph.slice(0,5).forEach(p => lines.push(`  - ${p.text}`)); }
  lines.push("ENFORCEMENT: Ensure outputs satisfy this capsule; otherwise abstain and request the minimal missing info.");
  lines.push("END CAPSULE","");
}
      }
    }
    if (prof && prof.response && prof.response.schema_ref){
      lines.push("SYSTEM: Attached Schema");
      pushSchemaTXT(prof.response.schema_ref);
    }
  }

  elOut.value = lines.join('\n');
}

// --- JSON export ---
function downloadJson(){
  const caps = collectSelections();
  const fmt = (document.getElementById('format')||{}).value || 'text';
  const mode = (document.getElementById('mode')||{}).value || 'verbose';
  const incAssumptions = (document.getElementById('incAssumptions')||{}).checked !== false;
  const incSocratic = (document.getElementById('incSocratic')||{}).checked !== false;
  const incAphorisms = (document.getElementById('incAphorisms')||{}).checked !== false;
  const snapshot = {};
  caps.forEach(c=> snapshot[c.id] = c);
  const payload = {
    loader: DEFAULT_LOADER,
    bootstrap: DEFAULT_BOOTSTRAP,
    profile: STATE.profile,
    selection: {
      capsule_ids: caps.map(c=>c.id),
      order: caps.map(c=>c.id),
      include: { assumptions: incAssumptions, socratic: incSocratic, aphorisms: incAphorisms },
      format: fmt, mode
    },
    snapshot_capsules: snapshot
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], {type:'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'truth_capsules_selection.json';
  document.body.appendChild(a); a.click(); a.remove();
  elStatus.textContent = 'Downloaded truth_capsules_selection.json'; setTimeout(()=> elStatus.textContent='', 1500);
}

// --- Share link ---
function shareLink(){
  const caps = collectSelections().map(c=>c.id);
  const bundles = [...STATE.selectedBundles];
  const fmt = (document.getElementById('format')||{}).value || 'text';
  const mode = (document.getElementById('mode')||{}).value || 'verbose';
  const ass = (document.getElementById('incAssumptions')||{}).checked !== false;
  const soc = (document.getElementById('incSocratic')||{}).checked !== false;
  const aph = (document.getElementById('incAphorisms')||{}).checked !== false;
  const qs = new URLSearchParams();
  if (caps.length) qs.set('caps', caps.join(','));
  if (bundles.length) qs.set('bundles', bundles.join(','));
  qs.set('fmt', fmt); qs.set('mode', mode);
  qs.set('ass', ass? '1':'0'); qs.set('soc', soc? '1':'0'); qs.set('aph', aph? '1':'0');
  qs.set('prof', STATE.profile || '');
  const url = `${location.origin}${location.pathname}?${qs.toString()}`;
  navigator.clipboard.writeText(url).then(()=>{
    elStatus.textContent='Shareable link copied'; setTimeout(()=> elStatus.textContent='', 1500);
  }, ()=>{
    elOut.value = url; elStatus.textContent='Copy failed; URL placed in output'; setTimeout(()=> elStatus.textContent='', 2000);
  });
}

// --- Bindings ---
document.getElementById('composeBtn').addEventListener('click', composePrompt);
document.getElementById('copyBtn').addEventListener('click', ()=>{
  elOut.select(); document.execCommand('copy');
  elStatus.textContent = 'Copied to clipboard'; setTimeout(()=> elStatus.textContent = '', 1500);
});
document.getElementById('downloadBtn').addEventListener('click', ()=>{
  const fmt = (document.getElementById('format')||{}).value || 'text';
  const ext = fmt === 'md' ? 'md' : 'txt';
  const blob = new Blob([elOut.value], {type:'text/plain'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `system_prompt.${ext}`;
  document.body.appendChild(a); a.click(); a.remove();
  elStatus.textContent = `Downloaded system_prompt.${ext}`; setTimeout(()=> elStatus.textContent = '', 1500);
});
document.getElementById('downloadJsonBtn').addEventListener('click', downloadJson);
document.getElementById('shareBtn').addEventListener('click', shareLink);
document.getElementById('q').addEventListener('input', render);
document.getElementById('format').addEventListener('change', ()=> { STATE.fmt = document.getElementById('format').value; saveState(STATE); });
document.getElementById('mode').addEventListener('change', ()=> { STATE.mode = document.getElementById('mode').value; saveState(STATE); });
document.getElementById('incAssumptions').addEventListener('change', ()=> { STATE.ass = document.getElementById('incAssumptions').checked; saveState(STATE); });
document.getElementById('incSocratic').addEventListener('change', ()=> { STATE.soc = document.getElementById('incSocratic').checked; saveState(STATE); });
document.getElementById('incAphorisms').addEventListener('change', ()=> { STATE.aph = document.getElementById('incAphorisms').checked; saveState(STATE); });
document.getElementById('profile').addEventListener('change', ()=> { STATE.profile = document.getElementById('profile').value; saveState(STATE); updateProfileDesc(); });

render();
</script>
</body>
</html>
"""

def safe_embed_json(obj):
    s = json.dumps(obj, ensure_ascii=False)
    return s.replace("</script>", "<\\/script>")

def build_spa(data, out_path, loader_text=None, title=None):
    loader_text = loader_text or DEFAULT_LOADER
    title = title or "Truth Capsule System Prompt Composer"
    doc = HTML_TEMPLATE
    doc = doc.replace("__TITLE__", html.escape(title))
    doc = doc.replace("__STAMP__", datetime.datetime.utcnow().isoformat())
    doc = doc.replace("__DATA__", safe_embed_json(data))
    doc = doc.replace("__LOADER__", safe_embed_json(loader_text))
    doc = doc.replace("__BOOT__", safe_embed_json(DEFAULT_BOOTSTRAP))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--loader")
    ap.add_argument("--title")
    args = ap.parse_args()

    capsules, bundles, profiles, schemas = collect(args.input)
    data = {"capsules": capsules, "bundles": bundles, "profiles": profiles, "schemas": schemas}
    loader_text = slurp(args.loader) if args.loader else None

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    build_spa(data, args.out, loader_text=loader_text, title=args.title)
    print(f"Wrote SPA -> {args.out}  | Capsules: {len(capsules)}  Bundles: {len(bundles)}  Profiles: {len(profiles)}  Schemas: {len(schemas)}")

if __name__ == "__main__":
    main()
