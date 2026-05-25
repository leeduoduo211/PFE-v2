from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[2]


def _project_metadata() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_python_metadata_matches_streamlit_cloud_runtime() -> None:
    project = _project_metadata()["project"]

    assert project["requires-python"] == ">=3.10"
    assert "Programming Language :: Python :: 3.9" not in project["classifiers"]


def test_streamlit_dependency_uses_supported_python_floor() -> None:
    optional_dependencies = _project_metadata()["project"]["optional-dependencies"]

    assert "streamlit>=1.54" in optional_dependencies["ui"]
    assert "streamlit>=1.54" in optional_dependencies["dev"]
