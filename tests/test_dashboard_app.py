from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_all_tabs_render_the_global_empty_state():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path)).run()
    assert not app.exception

    app.sidebar.multiselect[0].set_value([]).run()

    expected_message = "No test case executions found for the selected global filter criteria."
    assert [item.value for item in app.info].count(expected_message) == 4