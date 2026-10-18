"""Core pipeline: split text into clauses, match rules, explain locally."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import requests
import yaml

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3:4b"
RULES_PATH = (
    Path(__file__).resolve().parent.parent / "rules" / "lease_rules.yaml"
)
MAX_CLAUSE_CHARS = 1200
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
NUMBERED = re.compile(r"(?m)^(?=\s*\d+(?:\.\d+)*[.)]\s)")

PROMPT = (
    "You help tenants understand lease clauses. This is not legal advice.\n"
    "Rule that flagged the clause: {title}\n"
    'Clause: """{clause}"""\n'
    'Reply with JSON only: {{"plain_english": "...", '
    '"ask_before_signing": "..."}}\n'
    "plain_english: at most 2 sentences. Only use facts stated in the clause."
)


@dataclass
class Flag:
    """A clause that matched a rule, plus optional model output."""

    rule_id: str
    title: str
    severity: str
    clause: str
    why: str
    ask: str
    localize: str
    source: str
    explanation: dict | None = None
    tokens_per_sec: float | None = None
    error: str | None = None


def load_rules(path: Path = RULES_PATH) -> list[dict]:
    """Load rules from YAML and precompile their regex patterns."""
    with open(path, encoding="utf-8") as f:
        rules = yaml.safe_load(f)["rules"]
    for rule in rules:
        rule["_compiled"] = [
            re.compile(p, re.IGNORECASE | re.DOTALL) for p in rule["patterns"]
        ]
    return rules


def split_clauses(text: str, min_chars: int = 25) -> list[str]:
    """Split on blank lines and numbered headings; merge tiny fragments."""
    blocks = re.split(r"\n\s*\n", text.strip())
    pieces = [p.strip() for b in blocks for p in NUMBERED.split(b) if p.strip()]
    clauses: list[str] = []
    carry = ""
    for piece in pieces:
        merged = f"{carry} {piece}".strip()
        if len(merged) < min_chars:
            carry = merged
        else:
            clauses.append(merged)
            carry = ""
    if carry:
        clauses.append(carry)
    return clauses


def match_clauses(clauses: list[str], rules: list[dict]) -> list[Flag]:
    """Return one Flag per (clause, rule) pair that matches."""
    flags: list[Flag] = []
    for clause in clauses:
        for rule in rules:
            if any(p.search(clause) for p in rule["_compiled"]):
                flags.append(
                    Flag(
                        rule["id"], rule["title"], rule["severity"], clause,
                        rule["why"], rule["ask"], rule.get("localize", ""),
                        rule.get("source", "TODO"),
                    )
                )
    return flags


def explain_flag(flag: Flag, model: str = MODEL, timeout: int = 120) -> Flag:
    """Ask the local Ollama model to explain one flagged clause."""
    payload = {
        "model": model,
        "prompt": PROMPT.format(
            title=flag.title, clause=flag.clause[:MAX_CLAUSE_CHARS]
        ),
        "stream": False,
        "format": "json",
        "options": {"num_ctx": 4096, "num_predict": 200, "temperature": 0.2},
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        flag.explanation = json.loads(data["response"])
        flag.tokens_per_sec = data["eval_count"] / (data["eval_duration"] / 1e9)
    except (
        requests.RequestException, KeyError, ZeroDivisionError,
        json.JSONDecodeError,
    ) as exc:
        flag.error = f"{type(exc).__name__}: {exc}"
    return flag


def top_questions(flags: list[Flag], limit: int = 3) -> list[str]:
    """Pick the most important distinct questions, highest severity first."""
    questions: list[str] = []
    for flag in sorted(flags, key=lambda f: SEVERITY_ORDER.get(f.severity, 9)):
        if flag.ask not in questions:
            questions.append(flag.ask)
    return questions[:limit]


def draft_email(questions: list[str]) -> str:
    """Turn questions into a short email to the landlord."""
    lines = "\n".join(f"{i}. {q}" for i, q in enumerate(questions, 1))
    return (
        "Hi,\n\nThanks for sending the lease. Before I sign, could you "
        f"clarify a few points?\n\n{lines}\n\nThanks,\n[Your name]"
    )
