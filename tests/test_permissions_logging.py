import json
from pathlib import Path
import builtins
import pytest
from src.core import config_manager
from src.core.utils.logging import log_event, LOG_FILE

@pytest.fixture(autouse=True)
def clean_log_file(tmp_path, monkeypatch):
    """Redirect the consent log file to a temporary location for isolation."""
    test_log = tmp_path / "consent_log.json"
    monkeypatch.setattr("src.core.utils.LOG_FILE", test_log)
    yield test_log

@pytest.fixture(autouse=True)
def clean_config(tmp_path, monkeypatch):
    """Redirect config.json to a temp file for isolation."""
    test_cfg = tmp_path / "config.json"
    monkeypatch.setattr("src.core.config_manager._get_cfg_path", lambda: test_cfg)
    yield test_cfg


def test_log_event_creates_file(clean_log_file):
    """log_event() should create a file and write valid JSON."""
    log_event("API", "granted")

    assert clean_log_file.exists()
    data = json.loads(clean_log_file.read_text())
    assert len(data) == 1
    assert data[0]["service"] == "API"
    assert data[0]["status"] == "granted"
    assert "timestamp" in data[0]


def test_request_external_permission_granted(monkeypatch, clean_config, clean_log_file):
    """Simulate user typing 'y' for permission (granted)."""
    monkeypatch.setattr(builtins, "input", lambda _: "y")

    result = config_manager.request_external_service_permission("Test_Service")
    assert result is True

    # Check config was updated
    cfg = config_manager.read_cfg()
    assert cfg["external_allowed"] is True

    # Check log entry
    logs = json.loads(clean_log_file.read_text())
    assert logs[-1]["status"] == "granted"
    assert logs[-1]["service"] == "Test_Service"


def test_request_external_permission_denied(monkeypatch, clean_config, clean_log_file):
    """Simulate user typing 'n' for permission (denied)."""
    monkeypatch.setattr(builtins, "input", lambda _: "n")

    result = config_manager.request_external_service_permission("Test_Service")
    assert result is False

    # Check config updated
    cfg = config_manager.read_cfg()
    assert cfg["external_allowed"] is False

    # Check log entry
    logs = json.loads(clean_log_file.read_text())
    assert logs[-1]["status"] == "denied"
