"""Generic dotenv/credential resolution tests."""

from pathlib import Path

from app.utils import load_dotenv_file, resolve_named_secrets


def test_load_dotenv_file_parses_key_value_lines(tmp_path: Path) -> None:
    """Comments and blank lines are ignored; values are split on the first =."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# comment\n\nFOO=bar\nURL=https://example.com?x=1\n", encoding="utf-8"
    )
    values = load_dotenv_file(env_file)
    assert values == {"FOO": "bar", "URL": "https://example.com?x=1"}


def test_load_dotenv_file_missing_path_is_empty(tmp_path: Path) -> None:
    """A missing dotenv file resolves to an empty mapping, never an error."""
    assert load_dotenv_file(tmp_path / "does-not-exist.env") == {}


def test_resolve_named_secrets_only_includes_present_non_empty_values() -> None:
    """Only present, non-empty named variables are resolved."""
    resolved = resolve_named_secrets(
        {"login": "X_LOGIN", "password": "X_PASSWORD", "missing": "X_MISSING"},
        {"X_LOGIN": "12345", "X_PASSWORD": "", "X_OTHER": "unused"},
    )
    assert set(resolved) == {"login"}
    assert resolved["login"].get_secret_value() == "12345"
