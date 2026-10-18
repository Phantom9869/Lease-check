"""Interactive review workspace: one self-contained HTML document (no network)."""
from __future__ import annotations

from html import escape

from leasecheck.core import SEVERITY_ORDER, Flag

TAGS = {"high": "Push back", "medium": "Look closer", "low": "Good to know"}


def esc(text: object) -> str:
    return escape(" ".join(str(text).split()))


def _plain(flag: Flag) -> str:
    if isinstance(flag.explanation, dict) and flag.explanation.get("plain_english"):
        return str(flag.explanation["plain_english"])
    return flag.why


def build_workspace(clauses: list[str], flags: list[Flag], email: str, dark: bool = False) -> str:
    """Return a full HTML page: document panel, findings panel, all behavior."""
    index = {c: i for i, c in enumerate(clauses)}
    flags = sorted(flags, key=lambda f: (SEVERITY_ORDER.get(f.severity, 9), index.get(f.clause, 0)))
    fids: dict[str, list[str]] = {}
    for n, f in enumerate(flags):
        fids.setdefault(f.clause, []).append(f"f{n}")

    doc = []
    for i, clause in enumerate(clauses):
        ids = fids.get(clause, [])
        if ids:
            top = min((f for f in flags if f.clause == clause), key=lambda f: SEVERITY_ORDER.get(f.severity, 9))
            doc.append(
                f'<p class="clause flagged" id="c{i}" data-f="{" ".join(ids)}" data-sev="{top.severity}" '
                f'tabindex="0" role="button" aria-label="Clause {i + 1}, {TAGS[top.severity]}. Show finding">'
                f'<span class="hl">{esc(clause)}</span></p>'
            )
        else:
            doc.append(f'<p class="clause" id="c{i}">{esc(clause)}</p>')

    items = []
    for n, f in enumerate(flags):
        src = "Not yet checked against local law." if f.source == "TODO" else f"Source: {esc(f.source)}"
        fine = " ".join(x for x in (esc(f.localize), src) if x)
        if f.error:
            fine += " The local model was unavailable, so this is the rule's own explanation."
        text = " ".join((f.title, _plain(f), f.why, f.ask, f.clause)).lower()
        items.append(
            f'<article class="finding" id="f{n}" data-c="c{index.get(f.clause, 0)}" data-sev="{f.severity}" '
            f'data-text="{esc(text)}"><button class="fh" aria-expanded="false" aria-controls="b{n}">'
            f'<span class="dot"></span><span class="ft">{esc(f.title)}<small>{TAGS[f.severity]}, clause '
            f'{index.get(f.clause, 0) + 1}</small></span><span class="chev" aria-hidden="true"></span></button>'
            f'<div class="fb" id="b{n}" hidden><p>{esc(_plain(f))}</p><p><b>Ask:</b> {esc(f.ask)}</p>'
            f'<p class="fine">{fine}</p></div></article>'
        )

    counts = {s: sum(f.severity == s for f in flags) for s in TAGS}
    chips = f'<button class="chip" data-sev="all" aria-pressed="true">All {len(flags)}</button>' + "".join(
        f'<button class="chip" data-sev="{s}" aria-pressed="false">{TAGS[s]} {n}</button>'
        for s, n in counts.items() if n
    )
    qs = []
    seen: list[str] = []
    for f in flags:
        if f.ask not in seen:
            seen.append(f.ask)
    qs = "".join(f"<li>{esc(q)}</li>" for q in seen[:3])
    marked = len({f.clause for f in flags})
    body = (
        f'<main class="ws"><section class="pane" aria-label="Lease document"><header class="ph">'
        f'<h2>Lease</h2><span class="muted">{marked} of {len(clauses)} clauses flagged</span></header>'
        f'<div class="scroll doc">{"".join(doc)}</div></section>'
        f'<section class="pane" aria-label="Findings"><header class="ph"><div role="tablist" class="tabs">'
        f'<button role="tab" id="t1" aria-selected="true" aria-controls="p1">Findings</button>'
        f'<button role="tab" id="t2" aria-selected="false" aria-controls="p2">Before you sign</button></div>'
        f'<button id="all" class="link" type="button">Expand all</button></header>'
        f'<div id="p1" role="tabpanel" aria-labelledby="t1" class="tp"><div class="tools">'
        f'<div class="chips" role="group" aria-label="Filter by severity">{chips}</div>'
        f'<input id="q" type="search" placeholder="Search findings" aria-label="Search findings">'
        f'<p id="count" class="muted" aria-live="polite"></p></div><div class="scroll">{"".join(items)}'
        f'<div id="empty" hidden><p><b>No findings match.</b></p><p class="muted">Try a different word or '
        f'show all severities.</p><button id="clear" class="chip" type="button">Clear filters</button></div>'
        f'{"" if flags else NO_FLAGS}</div></div>'
        f'<div id="p2" role="tabpanel" aria-labelledby="t2" class="tp" hidden><div class="scroll">'
        f'<h3>Questions worth asking</h3><ol>{qs or "<li>No questions yet.</li>"}</ol><h3>Draft email</h3>'
        f'<textarea id="email" readonly rows="10" aria-label="Draft email">{escape(email)}</textarea>'
        f'<button id="copy" class="primary" type="button">Copy email</button> '
        f'<span id="copied" class="muted" role="status"></span></div></div></section></main>'
    )
    return f'<!doctype html><html lang="en" data-theme="{"dark" if dark else "light"}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>{CSS}</style></head><body>{body}<script>{JS}</script></body></html>'


NO_FLAGS = '<div><p><b>No rule matched.</b></p><p class="muted">That does not mean the lease is safe.</p></div>'

CSS = """
:root{--ink:#1b2430;--muted:#5a6676;--line:#ddd7ca;--blue:#3340b8;--sel:#f1f2fc;--paper:#fff;--abg:#eceefb;--afg:#2a3499;--btn:#3340b8;
--doc:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif}
[data-sev=high]{--c:#9a3324;--t:#f6dcd7}[data-sev=medium]{--c:#8a5a12;--t:#f6e7bf}[data-sev=low]{--c:#4a5668;--t:#e3e8ef}
[hidden]{display:none!important}
[data-theme=dark]{color-scheme:dark;--ink:#e8eaee;--muted:#9aa3b2;--line:#2e333d;--sel:#252a45;--blue:#a5acff;--paper:#1c1f26;--abg:#2a2f55;--afg:#c9ceff;--btn:#4b57d9}
[data-theme=dark] [data-sev=high]{--c:#ff9b8c;--t:rgba(224,98,80,.30)}[data-theme=dark] [data-sev=medium]{--c:#e9b44c;--t:rgba(214,160,40,.30)}[data-theme=dark] [data-sev=low]{--c:#a9b8cf;--t:rgba(140,160,190,.24)}
*{box-sizing:border-box}html,body{height:100%;margin:0}
body{font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink);background:transparent}
.ws{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(320px,1fr);gap:16px;height:100%}
.pane{background:var(--paper);border:1px solid var(--line);border-radius:10px;display:flex;flex-direction:column;min-height:0;overflow:hidden}
.ph{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 16px;border-bottom:1px solid var(--line)}
.ph h2{font-size:15px;margin:0}.muted{color:var(--muted);font-size:14px;margin:0}
.scroll{overflow:auto;flex:1;min-height:0;padding:12px 16px}.tp{display:flex;flex-direction:column;flex:1;min-height:0}
.doc{padding:20px 24px}
.clause{font:19px/1.75 var(--doc);margin:0 0 4px;padding:8px 12px;border-left:3px solid transparent;border-radius:4px}
.clause.flagged{cursor:pointer;border-left-color:var(--c)}
.hl{background:var(--t);padding:.1em .15em;border-radius:2px;-webkit-box-decoration-break:clone;box-decoration-break:clone}
.clause.dim{border-left-color:transparent}.clause.dim .hl{background:none}
.clause.sel{background:var(--sel);box-shadow:0 0 0 2px var(--blue) inset}
.tabs{display:flex;gap:4px}.tabs button,.link{font:inherit;font-size:14px;border:0;background:none;color:var(--muted);padding:6px 10px;border-radius:6px;cursor:pointer}
.tabs button[aria-selected=true]{background:var(--abg);color:var(--afg);font-weight:600}.link{color:var(--blue)}
.tools{padding:12px 16px 4px;border-bottom:1px solid var(--line)}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}
.chip{font:inherit;font-size:14px;border:1px solid var(--line);background:var(--paper);border-radius:999px;padding:4px 11px;cursor:pointer;color:var(--ink)}
.chip[aria-pressed=true]{background:var(--abg);border-color:var(--blue);color:var(--afg);font-weight:600}
#q{width:100%;background:var(--paper);color:var(--ink);font:inherit;padding:8px 10px;border:1px solid var(--line);border-radius:6px;margin-bottom:6px}
#count{margin-bottom:6px}
.finding{border-bottom:1px solid var(--line);margin:0 -16px;padding:0 16px}.finding[hidden]{display:none}
.finding.sel{background:var(--sel);box-shadow:inset 3px 0 0 var(--blue)}
.fh{all:unset;box-sizing:border-box;display:flex;align-items:center;gap:10px;width:100%;padding:12px 0;cursor:pointer}
.dot{flex:none;width:9px;height:9px;border-radius:50%;background:var(--c)}
.ft{flex:1;font-weight:600}.ft small{display:block;font-weight:400;color:var(--c);font-size:13px}
.chev{width:8px;height:8px;border:solid var(--muted);border-width:0 2px 2px 0;transform:rotate(45deg);margin-right:4px}
[aria-expanded=true] .chev{transform:rotate(-135deg)}
.fb{padding:0 0 12px 19px;font-size:15px}.fb p{margin:0 0 8px}.fine{color:var(--muted);font-size:13px}
.primary{font:inherit;font-weight:600;background:var(--btn);color:#fff;border:0;border-radius:6px;padding:8px 14px;cursor:pointer}
textarea{width:100%;background:var(--paper);color:var(--ink);font:14px/1.5 system-ui,sans-serif;border:1px solid var(--line);border-radius:6px;padding:10px;margin-bottom:10px;resize:vertical}
h3{font-size:14px;margin:8px 0}ol{padding-left:20px}li{margin-bottom:6px}
button:focus-visible,input:focus-visible,.clause:focus-visible,textarea:focus-visible{outline:2px solid var(--blue);outline-offset:2px}
@media(max-width:820px){.ws{grid-template-columns:1fr;height:auto}.scroll{overflow:visible}.pane{overflow:visible}body{overflow:auto}}
@media(prefers-reduced-motion:no-preference){.chev{transition:transform .15s}}
"""

JS = """
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
let sev='all',q='',sel=null;const total=$$('.finding').length;
function reveal(el){let p=el.parentElement;
 while(p&&p!==document.body&&!(/(auto|scroll)/.test(getComputedStyle(p).overflowY)&&p.scrollHeight>p.clientHeight))p=p.parentElement;
 const box=(p&&p!==document.body)?p:document.scrollingElement;if(!box||!box.scrollTo)return;
 const base=box===document.scrollingElement?0:box.getBoundingClientRect().top;
 box.scrollTo({top:Math.max(0,el.getBoundingClientRect().top-base+box.scrollTop-box.clientHeight/3),
 behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});}
function open(f,on){const b=$('.fh',f);b.setAttribute('aria-expanded',on);$('.fb',f).hidden=!on;}
function apply(){let n=0;$$('.finding').forEach(f=>{const ok=(sev==='all'||f.dataset.sev===sev)&&(!q||f.dataset.text.includes(q));f.hidden=!ok;n+=ok;});
 $$('.clause.flagged').forEach(c=>c.classList.toggle('dim',!c.dataset.f.split(' ').some(i=>!$('#'+i).hidden)));
 $('#count').textContent=total?`Showing ${n} of ${total} findings`:'';$('#empty').hidden=n>0||!total;}
function select(id,scroll=true){const f=$('#'+id);if(!f)return;if(f.hidden){sev='all';q='';$('#q').value='';syncChips();apply();}
 $$('.sel').forEach(e=>e.classList.remove('sel'));sel=id;f.classList.add('sel');const c=$('#'+f.dataset.c);c.classList.add('sel');open(f,true);
 if(scroll){reveal(c);reveal(f);}}
function syncChips(){$$('.chip[data-sev]').forEach(c=>c.setAttribute('aria-pressed',c.dataset.sev===sev));}
$$('.chip[data-sev]').forEach(c=>c.onclick=()=>{sev=c.dataset.sev;syncChips();apply();});
$('#q').oninput=e=>{q=e.target.value.trim().toLowerCase();apply();};
$('#clear').onclick=()=>{sev='all';q='';$('#q').value='';syncChips();apply();};
$$('.fh').forEach(b=>{const f=b.parentElement;b.onclick=()=>{const on=b.getAttribute('aria-expanded')!=='true';if(on)select(f.id);else{open(f,false);}};
 b.onkeydown=e=>{if(e.key!=='ArrowDown'&&e.key!=='ArrowUp')return;const v=$$('.finding:not([hidden]) .fh'),i=v.indexOf(b)+(e.key==='ArrowDown'?1:-1);if(v[i]){v[i].focus();e.preventDefault();}};});
$$('.clause.flagged').forEach(c=>{const go=()=>{const ids=c.dataset.f.split(' ');select(ids.find(i=>i===sel)||ids[0]);};
 c.onclick=go;c.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();go();}};});
let all=false;$('#all').onclick=()=>{all=!all;$$('.finding:not([hidden])').forEach(f=>open(f,all));$('#all').textContent=all?'Collapse all':'Expand all';};
$$('[role=tab]').forEach(t=>t.onclick=()=>{$$('[role=tab]').forEach(x=>{const on=x===t;x.setAttribute('aria-selected',on);$('#'+x.getAttribute('aria-controls')).hidden=!on;});
 $('#all').hidden=t.id!=='t1';});
$('#copy').onclick=async()=>{const t=$('#email'),m=$('#copied');t.select();let ok=false;
 try{await navigator.clipboard.writeText(t.value);ok=true;}catch(e){try{ok=document.execCommand('copy');}catch(e2){}}
 m.textContent=ok?'Copied':'Press Ctrl+C to copy';setTimeout(()=>m.textContent='',2500);};
apply();
"""
