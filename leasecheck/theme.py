"""Visual system for the LeaseCheck shell: light and dark tokens, CSS, static HTML."""
from __future__ import annotations

from html import escape

LIGHT = {"bg": "#f3f0e8", "surface": "#ffffff", "surface2": "#faf8f3", "line": "#d9d3c5", "line2": "#ebe6da",
         "ink": "#1b2430", "muted": "#566170", "lede": "#364152", "accent": "#3340b8", "accent-hover": "#2a3499",
         "link": "#3340b8", "amber": "#f6e7bf", "red": "#f6dcd7", "pen": "#9a3324", "ok": "#1f7a57", "warn": "#c47a0a",
         "alert-bg": "#fff4d6", "alert-line": "#e8cf8a", "err-bg": "#fde8e4", "err-line": "#e9b3a9",
         "shadow": "rgba(27,36,48,.05)", "ring": "rgba(51,64,184,.14)"}
DARK = {"bg": "#14161b", "surface": "#1c1f26", "surface2": "#20242c", "line": "#2e333d", "line2": "#272b34",
        "ink": "#e8eaee", "muted": "#9aa3b2", "lede": "#c3c9d4", "accent": "#4b57d9", "accent-hover": "#5c68ee",
        "link": "#a5acff", "amber": "rgba(214,160,40,.42)", "red": "rgba(224,98,80,.30)", "pen": "#ff9b8c",
        "ok": "#4cc38a", "warn": "#e9b44c", "alert-bg": "#2b2416", "alert-line": "#5a4a1f", "err-bg": "#33201d",
        "err-line": "#6b3a33", "shadow": "rgba(0,0,0,.35)", "ring": "rgba(120,130,255,.30)"}
SERIF = '"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif'

_BODY = """
html{font-size:18px}
html,body{background:var(--bg)}
[data-testid="stApp"]{background:var(--bg);color:var(--ink)}
[data-testid="stHeader"]{background:transparent}footer{display:none}
[data-testid="stMainBlockContainer"],.block-container{max-width:1440px;padding:1.4rem 2.5rem 3rem}
.st-key-top{border-bottom:1px solid var(--line);padding-bottom:1rem;margin-bottom:1.4rem;gap:0}
.lc-word{font:700 1.55rem SERIF;letter-spacing:-.01em;color:var(--ink)}
.lc-word span{font:400 .95rem system-ui,sans-serif;letter-spacing:0;color:var(--muted);margin-left:.9rem}
.lc-chipwrap{display:flex;justify-content:flex-end}
.lc-chip{display:inline-flex;gap:.55rem;align-items:center;font-size:.85rem;padding:.35rem .8rem;border:1px solid var(--line);
  background:var(--surface);border-radius:999px;color:var(--ink)}
.lc-chip i{width:.55rem;height:.55rem;border-radius:50%;background:var(--ok)}.lc-chip.warn i{background:var(--warn)}
.st-key-dark,.st-key-sample,.st-key-run{margin-left:auto!important}
[data-testid="stToggle"] p,[data-testid="stCheckbox"] p{color:var(--ink)!important;font-size:.95rem}
.lc-h1{font:700 3.3rem/1.05 SERIF;letter-spacing:-.025em;color:var(--ink);margin:0 0 1.2rem}
.lc-h1 mark,.lc-demo mark{color:inherit;border-radius:3px;-webkit-box-decoration-break:clone;box-decoration-break:clone}
.lc-h1 mark{background:linear-gradient(transparent 52%,var(--amber) 52%,var(--amber) 94%,transparent 94%);padding:0 .05em}
.lc-lede{font-size:1.15rem;line-height:1.6;color:var(--lede);margin:0 0 1.8rem;max-width:34rem;text-wrap:pretty}
.lc-demo{background:var(--surface);border:1px solid var(--line);border-radius:10px;display:grid;grid-template-columns:1.25fr 1fr;
  gap:1.2rem;padding:1.1rem 1.3rem;margin:0 0 1.8rem;max-width:38rem}
.lc-demo p{margin:0}.lc-demo .doc{font:1rem/1.7 SERIF;color:var(--ink)}.lc-demo mark{background:var(--red);padding:.1em .15em}
.lc-demo .note{border-left:3px solid var(--pen);padding-left:.85rem;font-size:.88rem;line-height:1.5;color:var(--ink)}
.lc-demo .note b{display:block;color:var(--pen)}
.lc-facts{display:grid;gap:.9rem;max-width:38rem;margin:0 0 .6rem}
.lc-fact{font-size:.95rem;line-height:1.5;color:var(--muted);padding-top:.85rem;border-top:1px solid var(--line)}
.lc-fact b{display:block;color:var(--ink);font-size:1rem}
.lc-lab{font-size:.95rem;font-weight:600;color:var(--ink)}
.lc-fine{color:var(--muted);font-size:.85rem;margin:.4rem 0 0}
.lc-alert{border:1px solid var(--alert-line);background:var(--alert-bg);color:var(--ink);border-radius:8px;padding:.7rem 1rem;
  font-size:.95rem;line-height:1.5;margin:0 0 1rem}.lc-alert.error{border-color:var(--err-line);background:var(--err-bg)}
.lc-load{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:1rem 1.3rem;max-width:36rem;margin:0 0 1.2rem}
.lc-load b{display:block;color:var(--ink);font-size:.98rem}
.lc-bar{height:6px;background:var(--line);border-radius:3px;overflow:hidden;margin-top:.75rem}
.lc-bar i{display:block;height:100%;background:var(--accent);border-radius:3px;transition:width .2s}
.st-key-editor{background:var(--surface);border:1px solid var(--line);border-radius:10px;gap:0;overflow:hidden;box-shadow:0 1px 2px var(--shadow)}
.st-key-editor:focus-within{border-color:var(--accent);box-shadow:0 0 0 3px var(--ring)}
.st-key-editor_bar{padding:.35rem .8rem .35rem 1.3rem;border-bottom:1px solid var(--line2)}
.st-key-editor_foot{padding:.75rem 1.3rem;border-top:1px solid var(--line2);background:var(--surface2)}
.st-key-editor [data-baseweb="textarea"],.st-key-editor [data-baseweb="base-input"],.st-key-editor textarea{
  border:0!important;background:var(--surface)!important;box-shadow:none!important;height:auto}
.st-key-editor textarea{font:1.1rem/1.7 SERIF!important;padding:1.2rem 1.4rem!important;color:var(--ink)!important;
  height:calc(100vh - 21rem)!important;min-height:26rem}
.st-key-editor [data-testid="stTextArea"],.st-key-editor [data-testid="stTextAreaRootElement"]{background:transparent!important}
.st-key-editor [data-testid="stTextArea"],.st-key-editor [data-testid="stTextArea"] *{border:0!important;box-shadow:none!important;outline:none!important}
.st-key-editor textarea::placeholder{color:var(--muted)!important;opacity:1}
.st-key-run button{background:var(--accent);border:1px solid var(--accent);height:2.7rem;padding:0 1.5rem;border-radius:8px;transition:background .12s}
.st-key-run button p{color:#fff!important;font-weight:600;font-size:1rem}
.st-key-run button:hover{background:var(--accent-hover);border-color:var(--accent-hover)}
.st-key-run button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.st-key-sample button,.st-key-updates button,.st-key-back button{color:var(--link);font-weight:600;padding:.2rem 0;min-height:2rem}
.st-key-sample button p,.st-key-updates button p,.st-key-back button p{color:var(--link)!important;font-size:.95rem}
.st-key-sample button:hover,.st-key-updates button:hover,.st-key-back button:hover{text-decoration:underline;background:transparent}
.st-key-dl button{height:2.3rem;min-height:2.3rem;border-radius:8px;border:1px solid var(--line)!important;background:var(--surface)!important}
.st-key-dl button p{color:var(--ink)!important}
@media(max-width:640px){.lc-word span{display:block;margin:.15rem 0 0}html{font-size:16px}.lc-h1{font-size:2.3rem}.st-key-top{margin-bottom:1.4rem}.lc-demo{grid-template-columns:1fr}
  .lc-chipwrap{justify-content:flex-start}.st-key-dark{margin-left:0!important}.st-key-editor textarea{height:22rem!important;min-height:0}}
"""


def css(dark: bool = False) -> str:
    """Tokens for the chosen mode followed by the shared stylesheet."""
    tokens = DARK if dark else LIGHT
    root = ":root{" + "".join(f"--{k}:{v};" for k, v in tokens.items()) + ("color-scheme:dark;" if dark else "") + "}"
    return root + _BODY.replace("SERIF", SERIF)


def wordmark_html() -> str:
    return '<div class="lc-word">LeaseCheck<span>Review a lease before you sign it.</span></div>'


def chip_html(ok: bool, message: str) -> str:
    text = "Rules verified by TUF" if ok else "Rules not verified fresh"
    return (f'<div class="lc-chipwrap"><span class="lc-chip{"" if ok else " warn"}" title="{escape(message)}">'
            f"<i></i>{text}</span></div>")


def loader_html(label: str, pct: int) -> str:
    return (f'<div class="lc-load" role="status"><b>{escape(label)}</b><div class="lc-bar">'
            f'<i style="width:{max(0, min(100, int(pct)))}%"></i></div></div>')


def hero_html(model_fact: str, rules_message: str) -> str:
    """Left column of the start screen. Arguments are already-escaped HTML."""
    return (
        '<div class="lc-h1" role="heading" aria-level="1">Know what you\u2019re <mark>signing.</mark></div>'
        '<p class="lc-lede">Paste a lease. LeaseCheck marks the clauses that deserve a second look, explains them in '
        "plain English and lists what to ask before you sign.</p>"
        '<div class="lc-demo" aria-label="Example"><p class="doc"><mark>Landlord may enter the unit at any time '
        'without notice.</mark></p><div class="note"><b>Push back</b>Ask for 24 to 48 hours\u2019 notice except in '
        "emergencies.</div></div>"
        '<div class="lc-facts"><div class="lc-fact"><b>Private by design</b>Everything runs on this computer. '
        f'Nothing is uploaded.</div><div class="lc-fact">{model_fact}</div>'
        f'<div class="lc-fact"><b>Signed rules</b>{rules_message}</div></div>'
    )
