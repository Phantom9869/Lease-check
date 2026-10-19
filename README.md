# LeaseCheck

A local-first tool that reads a lease with you before you sign it.

Paste the lease text. LeaseCheck shows it back as a marked-up page: clauses worth questioning are highlighted, and each one gets a note in plain English saying what it means and what to ask. It ends with the three most important questions to raise before signing and a draft email to the landlord.

Everything runs on your own computer. The lease is never uploaded, and the analysis works with Wi-Fi off.

Built for the Hacktoberfest Open-Source AI Challenge, Week 2: Side Hustle (October 12-18, 2026).
Write-up and demo: <!-- add the DEV post link here after publishing -->

## How it works

1. **Rules decide what gets flagged.** 11 rules in `rules/lease_rules.yaml` (entry without notice, automatic renewal, early-termination fees, non-refundable fees, deposit deductions, blanket repair duties, liability waivers, rent changes at the landlord's discretion, late fees, joint and several liability, subletting limits). Each has regex patterns, a severity, a plain-English reason, and a question to ask.
2. **Gemma 3 4B explains, locally.** For each flagged clause, a local model (through Ollama) writes a short plain-English explanation. It only ever sees short flagged clauses, never the whole lease. On a Ryzen 7 7730U laptop with 16 GB RAM and no dedicated GPU it generated at about 12.6 to 13.9 tokens per second. If the model is not running, the app falls back to each rule's own explanation.
3. **Rule updates are verified with TUF.** The rule pack is distributed as a [TUF](https://theupdateframework.io) repository (python-tuf). The app ships with a trusted root and checks signatures, hashes, version numbers and expiry before using an update. If an update is refused, it uses the last verified rules and shows a warning.

## Quick start (Windows PowerShell)

You need Python 3.10 or newer and [Ollama](https://ollama.com) with the model pulled (`ollama pull gemma3:4b`).

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python -m tools.tufrepo
python -m http.server 8000 --directory repo
```

Leave that server running. In a second terminal, with the venv activated:

```
streamlit run app.py
```

Click **Load sample lease**, then **Check lease**. The `tools.tufrepo` step generates your own signing keys in `keys/` (git-ignored) and publishes the signed rule pack. Run it again after editing `rules/lease_rules.yaml` to publish a new version.

## Attack demo

```
python -m tools.attack_demo
```

Serves doctored repositories from a local malicious mirror and prints the client's verdict:

| Attack | Client verdict | Reason |
|---|---|---|
| Honest repo | accepted | verified |
| Rule pack altered on the mirror | refused | LengthOrHashMismatchError |
| Rollback to older signed rules | refused | BadVersionNumberError |
| Stale metadata past its expiry | refused | ExpiredMetadataError |
| Forged timestamp, attacker's key | refused | UnsignedMetadataError |

## Project layout

- `app.py`: the Streamlit app (start screen, loading state, results, dark mode)
- `leasecheck/core.py`: clause splitting, rule matching, local model call
- `leasecheck/workspace.py`: the interactive review panel (self-contained HTML and JS, no network calls)
- `leasecheck/updates.py`: the TUF client that fetches and verifies the rule pack
- `leasecheck/theme.py`: light and dark styling
- `tools/tufrepo.py`: builds and signs the TUF repository; `tools/attack_demo.py`: the attack scenarios
- `rules/`, `samples/`: the rule pack and a synthetic sample lease
- `repo/`, `trusted/`: the signed repository and the trusted root the app ships with

## Limits

- The 11 rules are a starter set. They have **not** been checked against any jurisdiction's law, and each finding says so until a `source` is added to the rule.
- The demo keeps all four TUF role keys on one machine and skips delegations. A real deployment would keep the root and targets keys offline on hardware, with a threshold on root.
- TUF proves the rule pack is untampered and fresh. It does not prove the rules are correct.
- This is not legal advice, and a result with no flags does not mean a lease is safe.
- It has only been tried on the included synthetic sample lease, not on real leases or real users.

## Credits

Built with AI assistance (Claude). Uses [python-tuf](https://github.com/theupdateframework/python-tuf), [Streamlit](https://streamlit.io), [Ollama](https://ollama.com), Google's Gemma, and PyYAML.

## License

See `LICENSE`.
