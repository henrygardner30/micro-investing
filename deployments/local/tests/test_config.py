"""
Unit tests for configuration loading and ${VAR} environment expansion.

These are pure unit tests - no network, no credentials required.
"""

import textwrap

import pytest
from src.utils.config import expand_env_vars, load_config


def test_expand_replaces_set_variable(monkeypatch):
    """
    Verify a ${VAR} placeholder is replaced with the environment value when set.

    @PARAMS:
        - monkeypatch -> pytest fixture; sets ALPACA_API_KEY in the environment
    """
    monkeypatch.setenv("ALPACA_API_KEY", "real_key_123")
    assert expand_env_vars("${ALPACA_API_KEY}") == "real_key_123"


def test_expand_unset_variable_becomes_empty(monkeypatch):
    """
    Verify an unset ${VAR} placeholder resolves to "" rather than leaking the
    literal "${VAR}" string, which would otherwise be sent to the broker as an
    API key.

    @PARAMS:
        - monkeypatch -> pytest fixture; removes ALPACA_API_KEY from the environment
    """
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    assert expand_env_vars("${ALPACA_API_KEY}") == ""


def test_expand_is_recursive_over_dicts_and_lists(monkeypatch):
    """
    Verify expansion walks nested structures, replacing ${VAR} placeholders
    found inside dict values and list items.

    @PARAMS:
        - monkeypatch -> pytest fixture; sets the KEY and SECRET environment vars
    """
    monkeypatch.setenv("KEY", "abc")
    monkeypatch.setenv("SECRET", "xyz")
    config = {
        "alpaca": {"api_key": "${KEY}", "secret_key": "${SECRET}", "paper": True},
        "symbols": ["${KEY}", "VOO"],
    }
    expanded = expand_env_vars(config)
    assert expanded["alpaca"]["api_key"] == "abc"
    assert expanded["alpaca"]["secret_key"] == "xyz"
    assert expanded["symbols"] == ["abc", "VOO"]


def test_expand_preserves_non_string_scalars():
    """
    Verify non-string scalars (booleans, numbers, None) pass through unchanged,
    e.g. `paper: true` and allocation weights must not be coerced to strings.

    @PARAMS: None
    """
    assert expand_env_vars(True) is True
    assert expand_env_vars(0.6) == 0.6
    assert expand_env_vars(None) is None


def test_load_config_expands_env(tmp_path, monkeypatch):
    """
    Verify load_config reads a YAML file end-to-end and expands its ${VAR}
    placeholders from the environment while leaving non-string values intact.

    @PARAMS:
        - tmp_path    -> pytest fixture; temp dir the config.yml is written into
        - monkeypatch -> pytest fixture; sets ALPACA_API_KEY in the environment
    """
    monkeypatch.setenv("ALPACA_API_KEY", "pk_live_42")
    config_file = tmp_path / "config.yml"
    config_file.write_text(
        textwrap.dedent("""\
        alpaca:
          api_key: ${ALPACA_API_KEY}
          paper: true
    """)
    )

    config = load_config(str(config_file))

    assert config["alpaca"]["api_key"] == "pk_live_42"
    assert config["alpaca"]["paper"] is True


def test_load_config_missing_env_does_not_leak_placeholder(tmp_path, monkeypatch):
    """
    Verify load_config yields "" for a placeholder whose env var is unset,
    guarding the end-to-end path against shipping a literal "${VAR}" to Alpaca.

    @PARAMS:
        - tmp_path    -> pytest fixture; temp dir the config.yml is written into
        - monkeypatch -> pytest fixture; removes ALPACA_API_KEY from the environment
    """
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    config_file = tmp_path / "config.yml"
    config_file.write_text("alpaca:\n  api_key: ${ALPACA_API_KEY}\n")

    config = load_config(str(config_file))

    assert config["alpaca"]["api_key"] == ""


def test_load_config_missing_file_exits(tmp_path):
    """
    Verify load_config exits the process (SystemExit) when the config file path
    does not exist, rather than raising an unhandled error.

    @PARAMS:
        - tmp_path -> pytest fixture; supplies a temp dir to build a non-existent path
    """
    with pytest.raises(SystemExit):
        load_config(str(tmp_path / "does_not_exist.yml"))
