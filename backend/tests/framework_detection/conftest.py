import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"

for p in (str(ROOT), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)
        
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

MIN_RULES = {
    "rules_version": "test",
    "settings": {
        "exclude_dirs": ["node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next", ".git", "target", "docs", "examples", "tests"],
        "default_min_score": 0.7
    },
    "frameworks": {
        "React": {
            "min_score": 0.7,
            "signals": [
                {"type": "pkg_json_dep", "key": "dependencies", "contains": "react", "weight": 0.6},
                {"type": "import_snippet_any", "value": ["import React", "from 'react'"], "weight": 0.2},
            ],
        },
        "Django": {
            "min_score": 0.65,
            "signals": [
                {"type": "req_txt_contains", "value": "django", "weight": 0.6},
                {"type": "toml_dep", "key": "project.dependencies", "contains": "django", "weight": 0.6},
                {"type": "file_exists_glob", "value": ["**/manage.py", "**/config/settings/*.py"], "weight": 0.3},
            ],
        },
        "Webpack": {
            "min_score": 0.75,
            "signals": [
                {"type": "pkg_json_dep", "key": "devDependencies", "contains": "webpack", "weight": 0.5},
                {"type": "file_exists", "value": "webpack.config.js", "weight": 0.3},
                {"type": "pkg_json_script", "contains": "webpack", "weight": 0.2},
            ],
        },
        ".NET Console App": {
            "min_score": 0.7,
            "signals": [
                {"type": "csproj_contains", "contains": "<OutputType>Exe</OutputType>", "weight": 0.7},
                {"type": "csproj_contains", "contains": "<Project Sdk=\"Microsoft.NET.Sdk\">", "weight": 0.3},
            ],
        },
        "Flutter": {
            "min_score": 0.8,
            "signals": [
                {"type": "file_exists", "value": "pubspec.yaml", "weight": 0.2},
                {"type": "cfg_contains", "value": "dependencies:\n  flutter:", "weight": 0.5},
                {"type": "dir_exists_any", "value": ["lib", "android", "ios"], "weight": 0.2},
            ],
        },
    },
}

@pytest.fixture
def rules():
    return MIN_RULES

def make_files(base: Path, files: dict[str, str]):
    for rel, content in files.items():
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
