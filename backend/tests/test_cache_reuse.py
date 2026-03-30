import hashlib
from dataclasses import dataclass


def compute_project_tree_hash(files_meta: list[dict]) -> str:
    h = hashlib.sha256()
    items: list[tuple[str, str]] = []
    for m in files_meta:
        path = (m.get("path") or "").replace("\\", "/")
        ch = m.get("content_hash") or ""
        items.append((path, ch))
    items.sort(key=lambda x: x[0])
    for path, ch in items:
        h.update(path.encode("utf-8"))
        h.update(b"\0")
        h.update(ch.encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def test_analysis_key_stable_for_same_files():
    files = [
        {"path": "b.py", "content_hash": "bbb"},
        {"path": "a.py", "content_hash": "aaa"},
    ]

    tree = compute_project_tree_hash(files)
    key1 = hashlib.sha256(f"{tree}:1.0.0".encode("utf-8")).hexdigest()
    key2 = hashlib.sha256(f"{tree}:1.0.0".encode("utf-8")).hexdigest()

    assert key1 == key2


def test_analysis_key_changes_if_any_file_hash_changes():
    files1 = [
        {"path": "a.py", "content_hash": "aaa"},
    ]
    files2 = [
        {"path": "a.py", "content_hash": "DIFFERENT"},
    ]

    tree1 = compute_project_tree_hash(files1)
    tree2 = compute_project_tree_hash(files2)

    assert tree1 != tree2


# ---- Fake Project model (minimal) ----
@dataclass
class FakeProject:
    id: int
    analysis_key: str | None = None
    content_hash: str | None = None
    reused_from_project_id: int | None = None


# ---- Fake ProjectRepository that behaves like cache storage ----
class FakeProjectRepo:
    def __init__(self):
        self._projects: list[FakeProject] = []
        self._next_id = 1

    def create_project(self, **kwargs):
        p = FakeProject(
            id=self._next_id,
            analysis_key=kwargs.get("analysis_key"),
            content_hash=kwargs.get("content_hash"),
            reused_from_project_id=kwargs.get("reused_from_project_id"),
        )
        self._next_id += 1
        self._projects.append(p)
        return p

    def get_latest_by_analysis_key(self, analysis_key: str):
        matches = [p for p in self._projects if p.analysis_key == analysis_key]
        return matches[-1] if matches else None

    def update_timestamps(self, **kwargs):
        return None


# ---- Minimal AnalysisService harness ----
class MiniAnalysisService:
    def __init__(self, project_repo: FakeProjectRepo):
        self.project_repo = project_repo
        self.clone_calls: list[tuple[int, int]] = []

    def _clone_project_analysis(self, from_project_id: int, to_project_id: int):
        self.clone_calls.append((from_project_id, to_project_id))

    def run_cache_flow(
        self,
        file_list: list[dict],
        app_version: str = "1.0.0",
        *,
        use_cache: bool = True,
    ):
        # compute project hash
        def _compute_project_tree_hash(files_meta: list[dict]) -> str:
            h = hashlib.sha256()
            items = []
            for m in files_meta:
                path = (m.get("path") or "").replace("\\", "/")
                ch = m.get("content_hash") or ""
                items.append((path, ch))
            items.sort(key=lambda x: x[0])
            for path, ch in items:
                h.update(path.encode("utf-8"))
                h.update(b"\0")
                h.update(ch.encode("utf-8"))
                h.update(b"\n")
            return h.hexdigest()

        project_tree_hash = _compute_project_tree_hash(file_list)
        analysis_key = hashlib.sha256(
            f"{project_tree_hash}:{app_version}".encode("utf-8")
        ).hexdigest()

        cached = (
            self.project_repo.get_latest_by_analysis_key(analysis_key)
            if use_cache
            else None
        )

        # always create new project
        new_proj = self.project_repo.create_project(
            content_hash=project_tree_hash,
            analysis_key=analysis_key,
            reused_from_project_id=cached.id if cached else None,
        )

        # on hit, clone + early return
        if cached:
            self._clone_project_analysis(
                from_project_id=cached.id, to_project_id=new_proj.id
            )

        return new_proj, cached


def test_cache_reuse_creates_new_project_and_clones():
    repo = FakeProjectRepo()
    service = MiniAnalysisService(repo)

    files = [
        {"path": "a.py", "content_hash": "aaa"},
        {"path": "b.py", "content_hash": "bbb"},
    ]

    # first run -> miss
    p1, cached1 = service.run_cache_flow(files)
    assert cached1 is None
    assert p1.reused_from_project_id is None
    assert service.clone_calls == []

    # second run -> hit
    p2, cached2 = service.run_cache_flow(files)
    assert cached2 is not None
    assert p2.id != p1.id
    assert p2.analysis_key == p1.analysis_key
    assert p2.reused_from_project_id == p1.id
    assert service.clone_calls == [(p1.id, p2.id)]


def test_cache_toggle_off_does_not_set_reused_from_project_id_or_clone():
    repo = FakeProjectRepo()
    service = MiniAnalysisService(repo)

    files = [
        {"path": "a.py", "content_hash": "aaa"},
        {"path": "b.py", "content_hash": "bbb"},
    ]

    # Prime the cache with a normal run.
    p1, cached1 = service.run_cache_flow(files, use_cache=True)
    assert cached1 is None
    assert p1.reused_from_project_id is None

    # Same upload, but caching disabled.
    p2, cached2 = service.run_cache_flow(files, use_cache=False)

    # With caching disabled, we should behave like a miss.
    assert cached2 is None
    assert p2.reused_from_project_id is None
    assert service.clone_calls == []
