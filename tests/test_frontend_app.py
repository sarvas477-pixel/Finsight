"""Interactive smoke tests for the Streamlit frontend."""
from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_frontend_load_analyze_and_navigate():
    at = AppTest.from_file(Path(__file__).resolve().parents[1] / "app" / "app.py", default_timeout=20).run()
    assert not at.exception, at.exception

    at.button[0].click().run()
    assert not at.exception, at.exception
    assert at.session_state.df is not None
    assert len(at.session_state.df) == 5

    at.radio[0].set_value("Analyze").run()
    assert not at.exception, at.exception

    at.button[0].click().run()
    assert not at.exception, at.exception
    assert at.session_state.analyzed is True
    assert len(at.session_state.results) == 5

    summary = {
        "total": len(at.session_state.results),
        "clean": sum(r["status"] == "CLEAN" for r in at.session_state.results),
        "exceptions": sum(r["status"] == "EXCEPTION" for r in at.session_state.results),
        "review": sum(r["human_review_required"] for r in at.session_state.results),
    }
    assert summary == {"total": 5, "clean": 2, "exceptions": 3, "review": 3}

    at.radio[0].set_value("Evidence").run()
    assert not at.exception, at.exception
    assert len(at.selectbox) >= 1

    at.radio[0].set_value("Review").run()
    assert not at.exception, at.exception
    assert len(at.button) >= 1

    at.radio[0].set_value("Copilot").run()
    assert not at.exception, at.exception
    at.button.get_by_key("quick_Why is INV003 flagged?").click().run()
    assert not at.exception, at.exception
    assert at.session_state.chat
    assert "INV003" in at.session_state.chat[-1][1]

    at.radio[0].set_value("System").run()
    assert not at.exception, at.exception
