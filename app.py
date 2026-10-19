"""LeaseCheck UI. Run with: streamlit run app.py"""
import os
from html import escape
from pathlib import Path

import requests
import streamlit as st

HERE = Path(__file__).parent
REQUIRED = ["leasecheck/core.py", "leasecheck/updates.py", "leasecheck/workspace.py", "leasecheck/theme.py", "rules/lease_rules.yaml"]

st.set_page_config(page_title="LeaseCheck", page_icon="📑", layout="wide")
missing = [p for p in REQUIRED if not (HERE / p).exists()]
if missing:
    st.error("Some project files are missing or in the wrong folder: " + ", ".join(missing)
             + ". Re-extract the update from the project folder.")
    st.stop()

import yaml  # noqa: E402

from leasecheck.core import (  # noqa: E402
    MODEL, SEVERITY_ORDER, draft_email, explain_flag, load_rules, match_clauses, split_clauses, top_questions,
)
from leasecheck.theme import chip_html, css, hero_html, loader_html, wordmark_html  # noqa: E402
from leasecheck.updates import fetch_rules  # noqa: E402
from leasecheck.workspace import build_workspace  # noqa: E402

BASE = os.environ.get("LEASECHECK_REPO_URL", "http://localhost:8000")

if "dark" not in st.session_state:  # remembered in the URL (?theme=dark) so a reload keeps it
    st.session_state.dark = st.query_params.get("theme") == "dark"
dark = st.session_state.dark
st.markdown(f"<style>{css(dark)}</style>", unsafe_allow_html=True)


def note(text: str, kind: str = "warn") -> None:
    st.markdown(f'<div class="lc-alert {kind}" role="alert">{escape(text)}</div>', unsafe_allow_html=True)


def fine(text: str) -> None:
    st.markdown(f'<p class="lc-fine">{escape(text)}</p>', unsafe_allow_html=True)


def persist_theme() -> None:
    st.query_params["theme"] = "dark" if st.session_state.dark else "light"


def model_state() -> str:
    try:
        names = [m.get("name", "") for m in requests.get("http://localhost:11434/api/tags", timeout=1.5).json().get("models", [])]
    except (requests.RequestException, ValueError):
        return "offline"
    return "ready" if MODEL in names else "missing"


def check_updates() -> None:
    st.session_state.status = fetch_rules(f"{BASE}/metadata/", f"{BASE}/targets/")


def load_sample() -> None:
    st.session_state.lease_text = (HERE / "samples" / "sample_lease.txt").read_text(encoding="utf-8")


def analyze() -> None:
    if st.session_state.get("lease_text", "").strip():
        st.session_state.job = st.session_state.lease_text
    else:
        st.session_state.notice = "Paste a lease first, or load the sample lease."


def notes_markdown(clauses, flags, questions) -> str:
    lines = ["# Lease notes", "", f"{len({f.clause for f in flags})} of {len(clauses)} clauses flagged.", ""]
    for f in flags:
        lines += [f"## {f.title} ({f.severity})", f"> {' '.join(f.clause.split())}", "", f"Ask: {f.ask}", ""]
    return "\n".join(lines + ["## Questions to ask before signing", *[f"{i}. {q}" for i, q in enumerate(questions, 1)]])


if "status" not in st.session_state:
    check_updates()
status = st.session_state.status
view = st.session_state.setdefault("view", "input")

with st.container(key="top"):
    c1, c2, c3 = st.columns([6, 3, 2], vertical_alignment="center")
    c1.markdown(wordmark_html(), unsafe_allow_html=True)
    c2.markdown(chip_html(status.ok, status.message), unsafe_allow_html=True)
    c3.toggle("Dark mode", key="dark", on_change=persist_theme)

job = st.session_state.pop("job", None)
if job:
    ms = model_state() if st.session_state.get("use_model", True) else "off"
    try:
        rules = load_rules(status.rules_path)
    except (OSError, yaml.YAMLError, KeyError) as exc:
        note(f"Could not load the rules file ({type(exc).__name__}). Check rules/lease_rules.yaml.", "error")
        st.stop()
    slot = st.empty()
    slot.markdown(loader_html("Reading clauses", 8), unsafe_allow_html=True)
    clauses = split_clauses(job)
    slot.markdown(loader_html("Matching rules", 25), unsafe_allow_html=True)
    flags = match_clauses(clauses, rules)
    if ms == "ready" and flags:
        for i, flag in enumerate(flags):
            slot.markdown(loader_html(f"Explaining clause {i + 1} of {len(flags)} on this computer", 25 + 75 * i // len(flags)),
                          unsafe_allow_html=True)
            explain_flag(flag)
    slot.empty()
    flags.sort(key=lambda f: SEVERITY_ORDER.get(f.severity, 9))
    st.session_state.result = {"clauses": clauses, "flags": flags, "model": ms}
    st.session_state.view = view = "review"

notice = st.session_state.pop("notice", None)
if notice:
    note(notice)

if view == "input":
    ms = model_state()
    if ms == "ready":
        model_fact = f"<b>Plain-English notes</b>Written by {escape(MODEL)} on your own processor."
    else:
        model_fact = ("<b>Local model not running</b>You still get each rule's explanation. Start Ollama"
                      + (f" and run ollama pull {escape(MODEL)}" if ms == "missing" else "") + " for plain-English notes.")
    left, right = st.columns([5, 7], gap="large")
    with left:
        st.markdown(hero_html(model_fact, escape(status.message)), unsafe_allow_html=True)
        st.button("Check for rule updates", key="updates", type="tertiary", on_click=check_updates)
    with right:
        with st.container(key="editor"):
            with st.container(key="editor_bar"):
                b1, b2 = st.columns(2, vertical_alignment="center")
                b1.markdown('<span class="lc-lab">Lease text</span>', unsafe_allow_html=True)
                b2.button("Load sample lease", key="sample", type="tertiary", on_click=load_sample)
            st.text_area("Lease text", key="lease_text", height=440, label_visibility="collapsed",
                         placeholder="Paste the lease here. Numbered clauses work best.")
            with st.container(key="editor_foot"):
                f1, f2 = st.columns([3, 1], vertical_alignment="center")
                f1.checkbox(f"Explain flagged clauses with {MODEL}", key="use_model", value=True)
                f2.button("Check lease", key="run", type="primary", on_click=analyze)
else:
    result = st.session_state.get("result")
    if not result:
        st.session_state.view = "input"
        st.rerun()
    clauses, flags = result["clauses"], result["flags"]
    questions = top_questions(flags)
    t1, t2, _ = st.columns([1, 1.3, 8], vertical_alignment="center")
    t1.button("← Edit lease", key="back", type="tertiary", on_click=lambda: st.session_state.update(view="input"))
    t2.download_button("Download notes", notes_markdown(clauses, flags, questions), "lease-notes.md", "text/markdown", key="dl")
    if result["model"] != "ready" and st.session_state.get("use_model", True):
        note("The local model was not running, so explanations come from the rules. Start Ollama and check again for plain-English notes.")
    try:
        from streamlit.components.v1 import html as component_html
        component_html(build_workspace(clauses, flags, draft_email(questions) if questions else "", dark), height=760, scrolling=False)
    except Exception as exc:  # noqa: BLE001 - degrade to a plain list rather than a blank page
        note(f"The interactive view could not load ({type(exc).__name__}). Showing a plain list instead.")
        for f in flags:
            with st.expander(f"{f.title} ({f.severity})"):
                st.write(f.clause)
                st.write(f"Ask: {f.ask}")
    speeds = [f.tokens_per_sec for f in flags if f.tokens_per_sec]
    if speeds:
        fine(f"Explained on this computer with {MODEL} at about {sum(speeds) / len(speeds):.0f} tokens per second. Nothing was uploaded.")
    fine("Flags clauses worth asking about. Not legal advice.")
