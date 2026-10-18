"""HTML fragments for the Streamlit UI. All lease and model text is escaped."""
from __future__ import annotations

from html import escape

from leasecheck.core import MODEL, SEVERITY_ORDER, Flag
from leasecheck.updates import RuleStatus

TAGS = {"high": "Push back", "medium": "Look closer", "low": "Good to know"}


def esc(text: object) -> str:
    """Escape text for HTML; also neutralize $ so it is never read as math."""
    return escape(" ".join(str(text).split())).replace("$", "&#36;")


def status_box(status: RuleStatus) -> str:
    """Rule-pack status: whether the rules were verified fresh."""
    kind = "ok" if status.ok else "warn"
    title = "Rules verified" if status.ok else "Rules not verified fresh"
    return (
        f'<div class="lc-status {kind}"><span class="lc-dot"></span>'
        f"<div><strong>{title}</strong><br>{esc(status.message)}</div></div>"
    )


def _source(flag: Flag) -> str:
    if flag.source.startswith("http"):
        url = esc(flag.source)
        return f'Source: <a href="{url}" target="_blank" rel="noopener">{url}</a>'
    if flag.source == "TODO":
        return "This rule has not been checked against local law yet."
    return f"Source: {esc(flag.source)}"


def _note(flag: Flag) -> str:
    plain = ""
    if isinstance(flag.explanation, dict):
        plain = flag.explanation.get("plain_english", "")
    fine = [esc(flag.localize)] if flag.localize else []
    fine.append(_source(flag))
    if flag.error:
        fine.append("The local model was unavailable, so this is the rule's own explanation.")
    return (
        f'<div class="lc-note sev-{flag.severity}">'
        f'<div class="lc-tag">{TAGS.get(flag.severity, "Note")}</div>'
        f"<h4>{esc(flag.title)}</h4>"
        f"<p>{esc(plain or flag.why)}</p>"
        f'<p><b>Ask:</b> {esc(flag.ask)}</p>'
        f'<p class="lc-fine">{" ".join(fine)}</p></div>'
    )


def render_lease(clauses: list[str], flags: list[Flag]) -> str:
    """The lease as a marked-up page: clause on the left, notes in the margin."""
    by_clause: dict[str, list[Flag]] = {}
    for flag in flags:
        by_clause.setdefault(flag.clause, []).append(flag)
    rows = []
    for clause in clauses:
        found = sorted(
            by_clause.get(clause, []),
            key=lambda f: SEVERITY_ORDER.get(f.severity, 9),
        )
        if found:
            text = f'<span class="lc-mark sev-{found[0].severity}">{esc(clause)}</span>'
        else:
            text = esc(clause)
        notes = "".join(_note(f) for f in found)
        rows.append(
            f'<div class="lc-row"><p class="lc-clause">{text}</p>'
            f'<div class="lc-notes">{notes}</div></div>'
        )
    return '<div class="lc-paper">' + "".join(rows) + "</div>"


def summary(clauses: list[str], flags: list[Flag]) -> str:
    """One sentence plus a count per kind of note."""
    marked = len({f.clause for f in flags})
    counts = "".join(
        f'<span class="lc-count sev-{sev}"><b>{n}</b> {TAGS[sev]}</span>'
        for sev in ("high", "medium", "low")
        if (n := sum(f.severity == sev for f in flags))
    )
    lead = f"{marked} of {len(clauses)} clauses have notes"
    return f'<div class="lc-summary"><span class="lc-lead">{lead}</span>{counts}</div>'


def run_line(flags: list[Flag]) -> str:
    """Quiet footer saying how the explanations were produced."""
    speeds = [f.tokens_per_sec for f in flags if f.tokens_per_sec]
    if not speeds:
        return ""
    avg = sum(speeds) / len(speeds)
    return (
        f'<p class="lc-fine">Explained on this computer with {esc(MODEL)} '
        f"at about {avg:.0f} tokens per second. Nothing was uploaded.</p>"
    )


def questions_list(questions: list[str]) -> str:
    items = "".join(f"<li>{esc(q)}</li>" for q in questions)
    return f'<h3 class="lc-h">Before you sign, ask</h3><ol class="lc-questions">{items}</ol>'


def example() -> str:
    """Static example shown before the first check."""
    clause = (
        "2. Entry. Landlord may enter the unit at any time without notice "
        "to inspect or show the property."
    )
    flag = Flag(
        "entry_without_notice", "Landlord entry with little or no notice",
        "high", clause, "", "Can entry require at least 24-48 hours notice "
        "except in emergencies?", "", "example",
        explanation={"plain_english": "The landlord could walk in without warning."},
    )
    return (
        '<p class="lc-hint">Your lease will appear here with notes in the margin, '
        "like this clause:</p>" + render_lease([clause], [flag])
    )
