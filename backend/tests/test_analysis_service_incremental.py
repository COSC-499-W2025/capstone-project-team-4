import hashlib
import inspect
from pathlib import Path
from unittest.mock import MagicMock
from types import SimpleNamespace

import pytest
import src.services.analysis_service as analysis_service_mod
from src.services.analysis_service import AnalysisService

from dataclasses import dataclass
from datetime import datetime, timezone


@pytest.fixture(autouse=True)
def _patch_analysis_result(monkeypatch):
    class DummyAnalysisResult(SimpleNamespace):
        def __init__(self, **kwargs):
            # If pipeline passes None, force a valid datetime so tests can proceed
            if kwargs.get("zip_uploaded_at") is None:
                kwargs["zip_uploaded_at"] = datetime.now(timezone.utc)
            super().__init__(**kwargs)

    # Replace the Pydantic model with our dummy for tests
    monkeypatch.setattr(
        analysis_service_mod, "AnalysisResult", DummyAnalysisResult, raising=True
    )


@dataclass
class ProjectStub:
    id: int
    name: str = "proj"
    source_type: str = "zip"
    source_url: str = ""
    analysis_key: str = "analysiskey"
    content_hash: str = "treehash"


# ---------- Settings patch (do NOT mutate pydantic settings) ----------
class SettingsProxy:
    def __init__(self, base, **overrides):
        self._base = base
        self._overrides = overrides

    def __getattr__(self, name):
        if name in self._overrides:
            return self._overrides[name]
        return getattr(self._base, name)


@pytest.fixture(autouse=True)
def _patch_analysis_service_settings(monkeypatch):
    proxied = SettingsProxy(
        analysis_service_mod.settings,
        skip_analysis_cache=False,  # used by your pipeline
    )
    monkeypatch.setattr(analysis_service_mod, "settings", proxied, raising=True)


# ---------- Helpers ----------
def call_run_pipeline(svc, **kwargs):
    sig = inspect.signature(svc._run_analysis_pipeline)

    if "zip_uploaded_at" in sig.parameters and "zip_uploaded_at" not in kwargs:
        kwargs["zip_uploaded_at"] = datetime.now(timezone.utc)

    filtered = {k: v for k, v in kwargs.items() if k in sig.parameters}
    return svc._run_analysis_pipeline(**filtered)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


class FI:
    """Minimal FileInfo object compatible with file_info_to_metadata_dict()."""

    def __init__(self, rel: str, path: Path):
        self.relative_path = rel.replace("\\", "/")
        self.path = str(path)

        self.filename = self.relative_path.split("/")[-1]
        self.file_type = "text"
        self.language = "unknown"
        self.size = path.stat().st_size
        self.created = None
        self.modified = None
        self.lines_of_code = 1


def stub_heavy_pipeline(monkeypatch, svc: AnalysisService):
    """Make the pipeline fast and predictable."""
    monkeypatch.setattr(
        "src.services.analysis_service.git_analyze_contributors", lambda *a, **k: []
    )
    monkeypatch.setattr(
        "src.services.analysis_service.project_analysis_to_dict", lambda x: x
    )
    monkeypatch.setattr(
        "src.services.analysis_service.detect_libraries_recursive",
        lambda *a, **k: {"libraries": []},
    )
    monkeypatch.setattr(
        "src.services.analysis_service.detect_tools_recursive",
        lambda *a, **k: {"tools": []},
    )
    monkeypatch.setattr(
        "src.services.analysis_service.ProjectAnalyzer.analyze_project_languages",
        lambda *a, **k: [],
    )
    monkeypatch.setattr(
        svc, "_detect_frameworks_best", lambda *a, **k: [], raising=False
    )

    monkeypatch.setattr(
        svc, "_detect_skills", lambda *a, **k: {"skill_categories": {}}, raising=False
    )
    monkeypatch.setattr(svc, "_enhance_frameworks", lambda *a, **k: [], raising=False)

    # DB saves stubbed
    monkeypatch.setattr(svc, "_save_files", MagicMock(), raising=False)
    monkeypatch.setattr(svc, "_save_complexity", MagicMock(), raising=False)
    monkeypatch.setattr(svc, "_save_contributors", MagicMock(), raising=False)
    monkeypatch.setattr(svc, "_save_skills", MagicMock(), raising=False)
    monkeypatch.setattr(svc, "_save_frameworks", MagicMock(), raising=False)
    monkeypatch.setattr(svc, "_save_libraries", MagicMock(), raising=False)
    monkeypatch.setattr(svc, "_save_tools", MagicMock(), raising=False)

    # Hash helper (name varies; patch safely)
    monkeypatch.setattr(
        svc,
        "_compute_project_tree_hash",
        lambda *a, **k: ("treehash", "analysiskey"),
        raising=False,
    )

    svc.project_repo.get_latest_by_analysis_key = MagicMock(return_value=None)
    svc.project_repo.create_project = MagicMock(return_value=ProjectStub(id=999))


# ---------- Tests ----------
def test_incremental_disabled_when_use_cache_false(tmp_path, monkeypatch):
    svc = AnalysisService(db=MagicMock())
    svc.project_repo = MagicMock()
    svc.file_repo = MagicMock()
    svc._clone_files_and_complexity_for_paths = MagicMock()

    stub_heavy_pipeline(monkeypatch, svc)

    # real file exists
    (tmp_path / "a.txt").write_text("hello")
    file_info_list = [FI("a.txt", tmp_path / "a.txt")]
    monkeypatch.setattr(
        "src.services.analysis_service.collect_all_file_info",
        lambda *a, **k: file_info_list,
    )

    call_run_pipeline(
        svc,
        project_path=str(tmp_path),
        project_name="proj",
        source_type="zip",
        source_url="",
        use_cache=False,
        split_projects=False,
        user_id=None,
    )

    svc.project_repo.get_latest_by_name.assert_not_called()
    svc._clone_files_and_complexity_for_paths.assert_not_called()


def test_no_base_project_no_clone(tmp_path, monkeypatch):
    svc = AnalysisService(db=MagicMock())
    svc.project_repo = MagicMock()
    svc.file_repo = MagicMock()
    svc._clone_files_and_complexity_for_paths = MagicMock()

    stub_heavy_pipeline(monkeypatch, svc)

    (tmp_path / "a.txt").write_text("hello")
    file_info_list = [FI("a.txt", tmp_path / "a.txt")]
    monkeypatch.setattr(
        "src.services.analysis_service.collect_all_file_info",
        lambda *a, **k: file_info_list,
    )

    svc.project_repo.get_latest_by_name = MagicMock(return_value=None)

    call_run_pipeline(
        svc,
        project_path=str(tmp_path),
        project_name="proj",
        source_type="zip",
        source_url="",
        use_cache=True,
        split_projects=False,
        user_id=None,
    )

    svc._clone_files_and_complexity_for_paths.assert_not_called()


def test_base_rejected_when_overlap_too_small(tmp_path, monkeypatch):
    svc = AnalysisService(db=MagicMock())
    svc.project_repo = MagicMock()
    svc.file_repo = MagicMock()
    svc._clone_files_and_complexity_for_paths = MagicMock()

    stub_heavy_pipeline(monkeypatch, svc)

    # make 10 files
    file_info_list = []
    for i in range(10):
        p = tmp_path / f"f{i}.txt"
        p.write_text(f"content-{i}")
        file_info_list.append(FI(f"f{i}.txt", p))

    monkeypatch.setattr(
        "src.services.analysis_service.collect_all_file_info",
        lambda *a, **k: file_info_list,
    )

    svc.project_repo.get_latest_by_name = MagicMock(return_value=ProjectStub(id=99))

    svc.file_repo.get_path_hash_map = MagicMock(
        return_value={}
    )  # overlap 0.0 => reject

    call_run_pipeline(
        svc,
        project_path=str(tmp_path),
        project_name="proj",
        source_type="zip",
        source_url="",
        use_cache=True,
        split_projects=False,
        user_id=None,
    )

    svc._clone_files_and_complexity_for_paths.assert_not_called()


def test_clone_called_when_overlap_sufficient(tmp_path, monkeypatch):
    svc = AnalysisService(db=MagicMock())
    svc.project_repo = MagicMock()
    svc.file_repo = MagicMock()
    svc._clone_files_and_complexity_for_paths = MagicMock()

    stub_heavy_pipeline(monkeypatch, svc)

    # 4 files; 2 unchanged
    (tmp_path / "a.txt").write_text("same")
    (tmp_path / "b.txt").write_text("same")
    (tmp_path / "c.txt").write_text("new")
    (tmp_path / "d.txt").write_text("new2")

    file_info_list = [
        FI("a.txt", tmp_path / "a.txt"),
        FI("b.txt", tmp_path / "b.txt"),
        FI("c.txt", tmp_path / "c.txt"),
        FI("d.txt", tmp_path / "d.txt"),
    ]
    monkeypatch.setattr(
        "src.services.analysis_service.collect_all_file_info",
        lambda *a, **k: file_info_list,
    )

    svc.project_repo.get_latest_by_name = MagicMock(
        return_value=ProjectStub(id=42, name="proj", source_type="zip", source_url="")
    )

    base_map = {
        "a.txt": sha256_file(tmp_path / "a.txt"),
        "b.txt": sha256_file(tmp_path / "b.txt"),
    }
    svc.file_repo.get_path_hash_map = MagicMock(return_value=base_map)

    svc.project_repo.create_project = MagicMock(
        return_value=ProjectStub(id=99, name="proj", source_type="zip", source_url="")
    )

    call_run_pipeline(
        svc,
        project_path=str(tmp_path),
        project_name="proj",
        source_type="zip",
        source_url="",
        use_cache=True,
        split_projects=False,
        user_id=None,
    )

    svc._clone_files_and_complexity_for_paths.assert_called_once()
    _, kwargs = svc._clone_files_and_complexity_for_paths.call_args
    assert kwargs["from_project_id"] == 42
    assert kwargs["to_project_id"] == 99
    assert kwargs["paths_to_clone"] == {"a.txt", "b.txt"}


def test_complexity_only_runs_on_delta_paths(tmp_path, monkeypatch):
    svc = AnalysisService(db=MagicMock())
    svc.project_repo = MagicMock()
    svc.file_repo = MagicMock()
    svc._clone_files_and_complexity_for_paths = MagicMock()

    stub_heavy_pipeline(monkeypatch, svc)

    (tmp_path / "same.py").write_text("x=1")
    (tmp_path / "changed.py").write_text("x=2")

    file_info_list = [
        FI("same.py", tmp_path / "same.py"),
        FI("changed.py", tmp_path / "changed.py"),
    ]
    monkeypatch.setattr(
        "src.services.analysis_service.collect_all_file_info",
        lambda *a, **k: file_info_list,
    )

    svc.project_repo.create_project = MagicMock(
        return_value=ProjectStub(id=1, name="proj", source_type="zip", source_url="")
    )
    svc.file_repo.get_path_hash_map = MagicMock(
        return_value={"same.py": sha256_file(tmp_path / "same.py")}
    )

    svc.project_repo.create_project = MagicMock(return_value=ProjectStub(id=2))

    captured = {}

    def fake_analyze_project(project_path, paths):
        captured["paths"] = list(paths)
        return {"functions": []}

    monkeypatch.setattr(
        "src.services.analysis_service.analyze_project", fake_analyze_project
    )

    call_run_pipeline(
        svc,
        project_path=str(tmp_path),
        project_name="proj",
        source_type="zip",
        source_url="",
        use_cache=True,
        split_projects=False,
        user_id=None,
    )

    analyzed = sorted(Path(p).name for p in captured.get("paths", []))
    assert analyzed == ["changed.py"]


def test_save_files_only_saves_delta(tmp_path, monkeypatch):
    svc = AnalysisService(db=MagicMock())
    svc.project_repo = MagicMock()
    svc.file_repo = MagicMock()
    svc._clone_files_and_complexity_for_paths = MagicMock()

    stub_heavy_pipeline(monkeypatch, svc)

    (tmp_path / "same.txt").write_text("same")
    (tmp_path / "new.txt").write_text("new")

    file_info_list = [
        FI("same.txt", tmp_path / "same.txt"),
        FI("new.txt", tmp_path / "new.txt"),
    ]
    monkeypatch.setattr(
        "src.services.analysis_service.collect_all_file_info",
        lambda *a, **k: file_info_list,
    )

    svc.project_repo.get_latest_by_name = MagicMock(return_value=ProjectStub(id=10))
    svc.file_repo.get_path_hash_map = MagicMock(
        return_value={"same.txt": sha256_file(tmp_path / "same.txt")}
    )
    svc.project_repo.create_project = MagicMock(return_value=ProjectStub(id=11))

    save_files = MagicMock()
    monkeypatch.setattr(svc, "_save_files", save_files, raising=False)

    call_run_pipeline(
        svc,
        project_path=str(tmp_path),
        project_name="proj",
        source_type="zip",
        source_url="",
        use_cache=True,
        split_projects=False,
        user_id=None,
    )

    args, _ = save_files.call_args
    saved_file_list = args[1]
    saved_paths = sorted(f["path"] for f in saved_file_list)
    assert saved_paths == ["new.txt"]
