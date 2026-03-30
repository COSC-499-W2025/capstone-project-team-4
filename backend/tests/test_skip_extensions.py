from pathlib import Path

from src.core.analyzers.language import LanguageConfig, FileWalker


def test_should_analyze_file_skips_pdf_png_zip(tmp_path: Path):
    project = tmp_path / "proj"
    project.mkdir()
    # Create files with extensions that should be skipped
    (project / "a.pdf").write_bytes(b"%PDF-1.4\n" + b"x" * 200)
    (project / "b.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 200)
    (project / "c.zip").write_bytes(b"PK\x03\x04" + b"x" * 200)

    walker = FileWalker(LanguageConfig())
    # Analyzes if the files should be skipped
    assert walker.should_analyze_file(str(project / "a.pdf")) is False
    assert walker.should_analyze_file(str(project / "b.png")) is False
    assert walker.should_analyze_file(str(project / "c.zip")) is False


# Tests for FileWalker.should_analyze_file
def test_should_analyze_file_allows_html_py(tmp_path: Path):
    project = tmp_path / "proj"
    project.mkdir()
    # Create files with extensions that should be allowed
    (project / "index.html").write_text("<html>\n</html>\n", encoding="utf-8")
    (project / "main.py").write_text("print('hi')\n", encoding="utf-8")

    walker = FileWalker(LanguageConfig())

    assert walker.should_analyze_file(str(project / "index.html")) is True
    assert walker.should_analyze_file(str(project / "main.py")) is True
