# Lease check (local-first)

Setup (Windows PowerShell):

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt

Publish the rule pack and serve it (TUF-signed, keys stay in keys/):

    python -m tools.tufrepo
    python -m http.server 8000 --directory repo

Run the app (Ollama running with gemma3:4b pulled), in a second terminal:

    streamlit run app.py

Edit rules/lease_rules.yaml, bump `version:`, run `python -m tools.tufrepo`
again to publish. Re-running also extends metadata expiry (default 7 days).

Attack demo (prints a markdown table for the post):

    python -m tools.attack_demo

Before sharing: every rule has `source: TODO` and some have a `localize` note.
Verify each rule against official tenant-rights pages and fill those in.
Never commit keys/. Demo only: a real deployment keeps root/targets keys
offline on hardware, with a threshold on root.
