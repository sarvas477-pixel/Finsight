"""Shared repository paths used by CLI scripts and the Streamlit app."""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DEFAULT_INVOICE_CSV = DATA_DIR / "invoices.csv"


def resolve_csv(path: str | Path | None = None) -> Path:
    """Return a usable CSV path and fail with an actionable error."""
    candidate = Path(path) if path else DEFAULT_INVOICE_CSV
    if not candidate.is_absolute():
        candidate = ROOT_DIR / candidate
    candidate = candidate.resolve()
    if not candidate.is_file():
        raise FileNotFoundError(f"Invoice CSV not found: {candidate}")
    return candidate
