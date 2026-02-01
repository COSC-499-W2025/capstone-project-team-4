from pathlib import Path
from src.core.utils.project_detection import detect_project_roots


def test_detect_project_roots_prefers_multiple_subprojects(tmp_path: Path):
    """
    If 2+ subprojects exist, the top-level root should NOT be returned
    as a project root.
    """
    root = tmp_path / "root"
    root.mkdir()

    # Subproject 1 (package.json is commonly treated as project marker)
    p1 = root / "proj1"
    p1.mkdir()
    (p1 / "package.json").write_text('{"name":"proj1"}', encoding="utf-8")

    # Subproject 2 (pyproject.toml is commonly treated as project marker)
    p2 = root / "proj2"
    p2.mkdir()
    (p2 / "pyproject.toml").write_text("[project]\nname='proj2'\n", encoding="utf-8")

    roots = detect_project_roots(root)

    roots_set = set(r.resolve() for r in roots)
    assert p1.resolve() in roots_set
    assert p2.resolve() in roots_set
    assert root.resolve() not in roots_set
    assert len(roots_set) == 2
