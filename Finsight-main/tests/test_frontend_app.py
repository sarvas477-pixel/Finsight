"""Interactive smoke tests for the Streamlit frontend."""
from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_frontend_primary_workflow():
    at = AppTest.from_file(
        Path(__file__).resolve().parents[1] / "app" / "app.py",
        default_timeout=20,
    )
    # The application now has an authentication gate. Seed an authenticated
    # session for this workflow test so it exercises the actual workspace
    # rather than testing the login form.
    at.session_state["authenticated"] = True
    at.run()

    assert not at.exception, at.exception
    assert at.session_state.df is None
    assert len(at.button) >= 2

    # The primary workflow must be reachable from the first screen.
    at.button(key="load_sample").click().run()
    assert not at.exception, at.exception
    assert at.session_state.df is not None
    assert len(at.session_state.df) == 5

    # A keyed AppTest lookup returns the Button element itself, not a collection.
    at.button(key="analyze_btn").click().run()
    assert not at.exception, at.exception
    assert not at.error, [x.value for x in at.error]
    assert at.session_state.analyzed is True
    assert len(at.session_state.results) == 5

    summary = {
        "total": len(at.session_state.results),
        "clean": sum(r["status"] == "CLEAN" for r in at.session_state.results),
        "exceptions": sum(r["status"] == "EXCEPTION" for r in at.session_state.results),
        "review": sum(r["human_review_required"] for r in at.session_state.results),
    }
    assert summary == {"total": 5, "clean": 2, "exceptions": 3, "review": 3}

    # Results and the analysis tabs must exist after analysis.
    assert len(at.tabs) == 4
    assert len(at.selectbox) >= 1

    # Copilot quick action is still wired to the backend workflow.
    at.button(key="quick_Why is INV003 flagged?").click().run()
    assert not at.exception, at.exception
    assert at.session_state.chat
    assert "INV003" in at.session_state.chat[-1][1]
