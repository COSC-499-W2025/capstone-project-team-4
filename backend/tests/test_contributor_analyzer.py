import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

# Ensure backend is first on sys.path so `src` resolves to backend/src
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.core.analyzers import contributor as contributor_mod
from src.core.analyzers.contributor import analyze_contributors


def _run_git(cwd: str, args: list[str], env: dict | None = None) -> None:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"git {' '.join(args)} failed: {result.stderr}"


def _commit_file(
    repo_dir: str,
    rel_path: str,
    content: str,
    author_name: str,
    author_email: str,
    message: str,
) -> None:
    file_path = Path(repo_dir) / rel_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")

    _run_git(repo_dir, ["add", rel_path])

    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_NAME": author_name,
            "GIT_AUTHOR_EMAIL": author_email,
            "GIT_COMMITTER_NAME": author_name,
            "GIT_COMMITTER_EMAIL": author_email,
            "GIT_AUTHOR_DATE": "2024-01-01T00:00:00",
            "GIT_COMMITTER_DATE": "2024-01-01T00:00:00",
        }
    )
    _run_git(repo_dir, ["commit", "-m", message], env=env)


@pytest.mark.skipif(contributor_mod.Repo is None, reason="GitPython not installed")
def test_analyze_contributors_merges_noreply_and_email() -> None:
    with TemporaryDirectory() as tmp:
        _run_git(tmp, ["init", "-b", "main"])

        _commit_file(
            tmp,
            "file.txt",
            "line1\n",
            "Jaiden Lo",
            "jaidenlo@gmail.com",
            "first commit",
        )
        _commit_file(
            tmp,
            "file.txt",
            "line1\nline2\n",
            "Jaiden Lo",
            "12345+jaidenlo@users.noreply.github.com",
            "second commit",
        )

        result = analyze_contributors(project_path=tmp)

        assert len(result) == 1
        contributor = result[0]
        assert contributor["commits"] == 2
        assert contributor["email"].endswith("@gmail.com")


@pytest.mark.skipif(contributor_mod.Repo is None, reason="GitPython not installed")
def test_analyze_contributors_merges_similar_names() -> None:
    with TemporaryDirectory() as tmp:
        _run_git(tmp, ["init", "-b", "main"])

        _commit_file(
            tmp,
            "a.txt",
            "a\n",
            "AnLaxina",
            "anlaxina@gmail.com",
            "commit one",
        )
        _commit_file(
            tmp,
            "b.txt",
            "b\n",
            "Anilov Laxina",
            "anilov.laxina@outlook.com",
            "commit two",
        )

        result = analyze_contributors(project_path=tmp)

        assert len(result) == 1
        contributor = result[0]
        assert contributor["commits"] == 2
        assert contributor["name"] in {"AnLaxina", "Anilov Laxina"}
