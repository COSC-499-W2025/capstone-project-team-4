import json
from src.core import framework_detector as fd
from conftest import make_files

def test_react_min(tmp_path, rules):
    make_files(tmp_path, {
        "package.json": json.dumps({"dependencies": {"react": "18.3.0"}}),
        "src/index.jsx": "import React from 'react';\n",
    })
    res = fd.detect_frameworks_in_folder(tmp_path, rules)
    names = {r["name"] for r in res}
    assert "React" in names

def test_django_pyproject_and_manage(tmp_path, rules):
    make_files(tmp_path, {
        "pyproject.toml": '[project]\ndependencies=["django>=5.0"]\n',
        "manage.py": "import django\n",
        "config/settings/base.py": "INSTALLED_APPS=[]\n",
    })
    res = fd.detect_frameworks_in_folder(tmp_path, rules)
    assert any(r["name"]=="Django" for r in res)

def test_min_score_blocks_webpack(tmp_path, rules):
    make_files(tmp_path, {
        "package.json": json.dumps({"devDependencies": {"webpack": "5.0.0"}}),
    })
    res = fd.detect_frameworks_in_folder(tmp_path, rules)
    assert all(r["name"]!="Webpack" for r in res)

def test_exclude_dirs_effect(tmp_path, rules):
    make_files(tmp_path, {
        "node_modules/foo/package.json": json.dumps({"dependencies": {"react": "18.3.0"}}),
        "src/app.jsx": "import React from 'react';\n",
    })
    res = fd.detect_frameworks_in_folder(tmp_path, rules)
    assert res == []

def test_flutter_min(tmp_path, rules):
    make_files(tmp_path, {
        "pubspec.yaml": "name: demo\ndependencies:\n  flutter:\n    sdk: flutter\n",
        "lib/main.dart": "void main() { runApp(MyApp()); }\n",
        "android/.keep": "",
        "ios/.keep": "",
    })
    res = fd.detect_frameworks_in_folder(tmp_path, rules)
    assert any(r["name"]=="Flutter" for r in res)
