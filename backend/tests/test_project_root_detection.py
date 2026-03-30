from pathlib import Path


from src.core.utils.project_detection import detect_project_roots


def test_detect_project_roots_collapses_monorepo_to_root(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()

    (root / ".gitignore").write_text("node_modules/\n", encoding="utf-8")

    frontend = root / "frontend"
    frontend.mkdir()
    (frontend / "package.json").write_text('{"name":"frontend"}', encoding="utf-8")

    backend = root / "backend"
    backend.mkdir()
    (backend / "pyproject.toml").write_text(
        "[project]\nname='backend'\n", encoding="utf-8"
    )

    roots = detect_project_roots(root, max_depth=4)

    assert roots == [root.resolve()]


def test_detect_project_roots_single_project_returns_that_project(tmp_path: Path):
    root = tmp_path / "single"
    root.mkdir()

    # single project marker
    (root / "package.json").write_text('{"name":"single"}', encoding="utf-8")

    roots = detect_project_roots(root, max_depth=4)

    assert roots == [root.resolve()]


def test_detect_project_roots_multiple_projects_returns_multiple_roots(tmp_path: Path):
    container = tmp_path / "bundle"
    container.mkdir()

    p1 = container / "proj1"
    p1.mkdir()
    (p1 / "package.json").write_text('{"name":"p1"}', encoding="utf-8")

    p2 = container / "proj2"
    p2.mkdir()
    (p2 / "pyproject.toml").write_text("[project]\nname='p2'\n", encoding="utf-8")

    roots = detect_project_roots(container, max_depth=4)

    # Should detect both project roots (order may vary)
    root_paths = {r.resolve() for r in roots}
    assert root_paths == {p1.resolve(), p2.resolve()}
