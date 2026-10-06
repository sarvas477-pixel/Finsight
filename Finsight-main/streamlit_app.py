"""Streamlit Community Cloud entrypoint for FinSight."""
from __future__ import annotations
from pathlib import Path
import sys

# Add project root to sys.path for imports to work on Streamlit Cloud
ROOT = Path(__file__).resolve().parent
for candidate in (ROOT, ROOT.parent):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

# Now import and run the app
from app.app import main

if __name__ == "__main__":
    main()
