import textwrap
from pathlib import Path

import pytest

from src.core.python_code_features import (
    analyze_python_code,
    analyze_python_path,
    PythonFileFeatures,
)


def test_analyze_python_code_simple_loops_and_ds():
    code = textwrap.dedent(
        """
        def f(xs):
            total = 0
            for x in xs:
                total += x
            while total > 0:
                total -= 1
            data = [1, 2, 3]
            mapping = {"a": 1, "b": 2}
            s = {1, 2, 3}
            t = (1, 2, 3)
            comp = [x * 2 for x in xs]
            return total
        """
    )

    result = analyze_python_code(code, filename="sample.py")
    assert isinstance(result, PythonFileFeatures)
    assert result.ok is True
    assert result.error is None

    # loops
    loop_kinds = {l.kind for l in result.loops}
    assert loop_kinds == {"for", "while"}
    # at least two loops detected
    assert len(result.loops) == 2

    # data structures
    ds_kinds = {d.kind for d in result.data_structures}
    # we expect literals + one list comprehension
    assert "list_literal" in ds_kinds
    assert "dict_literal" in ds_kinds
    assert "set_literal" in ds_kinds
    assert "tuple_literal" in ds_kinds
    assert "list_comp" in ds_kinds


def test_analyze_python_code_syntax_error():
    bad_code = "def oops(:\n    pass\n"
    result = analyze_python_code(bad_code, filename="bad.py")

    assert result.ok is False
    assert "SyntaxError" in (result.error or "")
    assert result.loops == []
    assert result.data_structures == []


def test_analyze_python_path_single_file(tmp_path: Path):
    file_path = tmp_path / "example.py"
    file_path.write_text(
        textwrap.dedent(
            """
            def g():
                data = [1, 2, 3]
                for i in data:
                    print(i)
            """
        ),
        encoding="utf-8",
    )

    report = analyze_python_path(file_path)

    assert report["root"] == str(file_path)
    summary = report["summary"]
    assert summary["files_analyzed"] == 1
    assert summary["files_ok"] == 1
    assert summary["total_loops"] == 1
    assert summary["total_data_structures"] >= 1
    assert summary["max_loop_nesting"] == 0

    files = report["files"]
    assert len(files) == 1
    assert files[0]["path"].endswith("example.py")
    assert len(files[0]["loops"]) == 1


def test_analyze_python_path_directory_multiple_files(tmp_path: Path):
    # file 1: one for-loop and a list
    f1 = tmp_path / "a.py"
    f1.write_text(
        "for i in [1, 2, 3]:\n    print(i)\n",
        encoding="utf-8",
    )

    # file 2: nested loops and a dict
    f2 = tmp_path / "b.py"
    f2.write_text(
        textwrap.dedent(
            """
            def nested(xs):
                for x in xs:
                    while x > 0:
                        x -= 1
                d = {"k": xs}
            """
        ),
        encoding="utf-8",
    )

    report = analyze_python_path(tmp_path)

    summary = report["summary"]
   
    assert summary["files_analyzed"] == 2
    assert summary["files_ok"] == 2

    # should see at least 3 loops (1 in a.py, 2 in b.py)
    assert summary["total_loops"] >= 3
    assert summary["max_loop_nesting"] >= 1

    ds_by_kind = summary["data_structures_by_kind"]
    # we know we used a list literal and a dict literal
    assert "list_literal" in ds_by_kind
    assert "dict_literal" in ds_by_kind


def test_analyze_python_path_non_python(tmp_path: Path):
    # non-python file
    txt = tmp_path / "not_python.txt"
    txt.write_text("just some text", encoding="utf-8")

    report = analyze_python_path(txt)

    assert report["summary"]["ok"] is False
    assert "Not a .py file or directory" in report["summary"]["error"]
    assert report["files"] == []
