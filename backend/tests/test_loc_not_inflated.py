from pathlib import Path
from src.core.analyzers.language import ProjectAnalyzer

def test_loc_does_not_count_pdf_or_images(tmp_path: Path):
    """
    Regression test: PDFs/images should be skipped and NOT inflate LOC.
    """
    project = tmp_path / "proj"
    project.mkdir()

    # 5 text lines in HTML
    (project / "lab1.html").write_text(
        "<html>\n<body>\nHello\n</body>\n</html>\n",
        encoding="utf-8",
    )

    # Big fake PDF (used to create huge line counts if read as text)
    (project / "instructions.pdf").write_bytes(b"%PDF-1.4\n" + b"\x00" * 100_000)

    # Fake PNG header + lots of bytes
    (project / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100_000)

    analyzer = ProjectAnalyzer()
    stats_by_lang = analyzer.analyze_project_lines_of_code(str(project))

    total_lines = sum(s.total_lines for s in stats_by_lang.values())
    total_code_lines = sum(s.code_lines for s in stats_by_lang.values())

    # Only the HTML file should contribute.
    assert total_lines == 5
    assert total_code_lines == 5