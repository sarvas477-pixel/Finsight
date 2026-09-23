"""Day 10 — quality guard.

The implementation lives in ``src/quality_guard.py`` (it's imported by both
the pipeline and the tests, so it needed a name that isn't a day number).
This module just re-exports it so the day-by-day file naming from the plan
still lines up with a real file.
"""
from src.quality_guard import create_quality_checked_result, template_result

__all__ = ["create_quality_checked_result", "template_result"]
