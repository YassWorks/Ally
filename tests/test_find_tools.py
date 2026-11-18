from app.src.tools.find_tools import find_declaration, find_references


def test_find_references_exact_match(tmp_path):
    (tmp_path / "a.py").write_text(
        "x = 1\nvalue = compute_total(x)\n", encoding="utf-8"
    )

    result = find_references.invoke(
        {"dir_path": str(tmp_path), "query": "compute_total"}
    )

    assert "a.py:2:" in result


def test_find_references_skips_ignored_dirs(tmp_path):
    ignored = tmp_path / "node_modules"
    ignored.mkdir()
    (ignored / "lib.js").write_text("needle\n", encoding="utf-8")

    result = find_references.invoke({"dir_path": str(tmp_path), "query": "needle"})

    assert "node_modules" not in result


def test_find_declaration(tmp_path):
    (tmp_path / "m.py").write_text("def build_graph():\n    pass\n", encoding="utf-8")

    result = find_declaration.invoke(
        {"dir_path": str(tmp_path), "symbol": "build_graph"}
    )

    assert "m.py:1:" in result


def test_only_exact_ignored_names_are_skipped(tmp_path):
    for folder in ("login", "logs"):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "auth.py").write_text("needle = 1\n", encoding="utf-8")
    (tmp_path / ".env").write_text("needle=secret\n", encoding="utf-8")

    result = find_references.invoke({"dir_path": str(tmp_path), "query": "needle"})

    assert "login" in result
    assert "logs" not in result
    assert ".env" not in result
