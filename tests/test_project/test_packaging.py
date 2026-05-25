from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_dev_extra_includes_ui_test_dependencies():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    dev_section = pyproject.split("dev = [", 1)[1].split("]", 1)[0]

    assert '"streamlit>=1.54"' in dev_section
    assert '"plotly>=5.18"' in dev_section


def test_devcontainer_installs_project_ui_extra():
    devcontainer = (ROOT / ".devcontainer" / "devcontainer.json").read_text(
        encoding="utf-8"
    )

    assert "pip3 install --user -e" in devcontainer
    assert ".[ui]" in devcontainer
