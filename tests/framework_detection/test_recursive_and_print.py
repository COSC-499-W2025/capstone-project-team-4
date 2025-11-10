import json
import yaml
from src.core import framework_detector as fd
from conftest import make_files

def test_recursive_and_print(tmp_path, rules, capsys):
    make_files(tmp_path / "apps/a", {
        "package.json": json.dumps({"dependencies": {"react": "18.3.0"}}),
        "src/index.jsx": "import React from 'react';\n",
    })
    make_files(tmp_path / "apps/b", {
        "pyproject.toml": '[project]\ndependencies=["django>=5"]\n',
        "manage.py": "import django\n",
        "config/settings/base.py": "INSTALLED_APPS=[]\n",
    })

    rules_path = tmp_path / "rules.yml"
    rules_path.write_text(yaml.safe_dump(rules), encoding="utf-8")

    res = fd.detect_frameworks_recursive(tmp_path, str(rules_path))
    assert "apps/a" in res["frameworks"] and "apps/b" in res["frameworks"]
    assert any(fw["name"]=="React" for fw in res["frameworks"]["apps/a"])
    assert any(fw["name"]=="Django" for fw in res["frameworks"]["apps/b"])

    fd.pretty_print_results(res)
    out = capsys.readouterr().out
    assert "Frameworks detected in:" in out
    assert "apps/a" in out and "apps/b" in out
