import pytest
from core import config_manager
from src.main import check_virtual_env


# Placeholder test functions for basic functionality
def add(a, b):
    return a + b


def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0


def test_add_negative():
    assert add(-2, -3) == -5
    assert add(-1, -1) == -2


def test_add_floats():
    assert add(2.5, 3.5) == 6.0
    assert add(-1.0, 1.0) == 0.0


def test_default_config_when_no_file(tmp_path):
    cfg_path = config_manager._get_cfg_path()
    if cfg_path.exists():
        cfg_path.unlink()
    cfg = config_manager.read_cfg()
    assert cfg["consent_granted"] is False
    assert cfg["external_allowed"] is False
    config_manager.set_consent(True)
    cfg_after = config_manager.read_cfg()
    assert cfg_after["consent_granted"] is True



def test_set_and_get_consent(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKMINE_HOME", str(tmp_path))
    config_manager.set_consent(True)
    cfg = config_manager.read_cfg()
    assert cfg["consent_granted"] is True

def test_set_and_get_consent():
    config_manager.set_consent(True)
    cfg = config_manager.read_cfg()
    assert cfg["consent_granted"] is True

    config_manager.set_consent(False)
    cfg = config_manager.read_cfg()
    assert cfg["consent_granted"] is False



def test_require_consent_block():
    cfg_path = config_manager._get_cfg_path()
    if cfg_path.exists():
        cfg_path.unlink()
    cfg = config_manager.read_cfg()
    assert cfg["consent_granted"] is False
    with pytest.raises(SystemExit):
        config_manager.require_consent()
