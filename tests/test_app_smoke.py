"""
test_app_smoke.py - Headless UI smoke test via streamlit.testing.
Boots the full app and walks the Back Office tab: run cash application,
build the collections queue, send a reminder — no exceptions allowed.
"""

from streamlit.testing.v1 import AppTest


def click_button(at, label_fragment):
    for i, b in enumerate(at.button):
        if label_fragment in b.label:
            return at.button[i].click().run()
    raise AssertionError(f"No button matching {label_fragment!r}; "
                         f"found {[b.label for b in at.button]}")


def test_app_boots_without_exception():
    at = AppTest.from_file("app.py", default_timeout=15).run()
    assert not at.exception


def test_back_office_full_walkthrough():
    at = AppTest.from_file("app.py", default_timeout=15).run()

    at = click_button(at, "Run Cash Application")
    assert not at.exception
    # KPI metrics appear after the run
    metric_labels = [m.label for m in at.metric]
    assert "Auto-Match Rate" in metric_labels

    at = click_button(at, "Build Collections Queue")
    assert not at.exception

    at = click_button(at, "Send reminder")
    assert not at.exception

    # The duplicate-send demo path must also not crash
    at = click_button(at, "Retry same send")
    assert not at.exception
