"""Wiring smoke test for the Streamlit app.

This does NOT assert anything about layout, labels, or widget counts —
per project policy the UI rendering layer is exempt from tests (the
functions app.py calls are tested directly instead). What this test
does catch is import/wiring breakage: a bad import, a renamed function
in uk_stress_benchmark, a typo in a variable name, or any other error
that would blow up the app before a single element renders. Assertions
are deliberately loose so the test survives an in-flight UI redesign.
"""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parent.parent / "app.py"


def test_app_runs_without_exception():
    # Model calibration on first run can take a while, so give it plenty
    # of headroom rather than tuning a tight timeout.
    at = AppTest.from_file(str(APP_PATH), default_timeout=120)
    at.run()

    assert not at.exception

    # Something substantive rendered — at least one element or widget
    # exists in the main body. Not checking *which* one, since the UI
    # is being redesigned concurrently with this test.
    assert len(at.main.children) > 0
