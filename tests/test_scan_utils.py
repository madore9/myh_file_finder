import os

import scan_utils


def test_should_skip_hidden_and_known_dir_names():
    assert scan_utils.should_skip_dir(".git") is True
    assert scan_utils.should_skip_dir("node_modules") is True
    assert scan_utils.should_skip_dir("__pycache__") is True
    assert scan_utils.should_skip_dir(".hidden", include_hidden=False) is True
    assert scan_utils.should_skip_dir(".hidden", include_hidden=True) is False


def test_should_skip_suffix_system_and_volume_paths_on_mac(monkeypatch):
    monkeypatch.setattr(scan_utils, "IS_MAC", True)
    assert scan_utils.should_skip_dir("MyApp.app") is True
    assert scan_utils.should_skip_dir("usr", "/usr") is True
    assert scan_utils.should_skip_dir("System", "/System") is True
    assert scan_utils.should_skip_dir("tm", "/Volumes/Time Machine Backups/MyDisk") is True
    assert scan_utils.should_skip_dir("normal_dir", "/Users/me/normal_dir") is False


def test_should_skip_excluded_realpath(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    blocked = root / "blocked"
    child = blocked / "child"
    child.mkdir(parents=True)

    excluded = {str(blocked.resolve())}
    assert scan_utils.should_skip_dir("blocked", str(blocked), excluded_dirs=excluded) is True
    assert scan_utils.should_skip_dir("child", str(child), excluded_dirs=excluded) is True


def test_fast_scandir_filters_hidden_and_skipped(tmp_path):
    top = tmp_path / "scan"
    top.mkdir()
    (top / "visible.txt").write_text("x", encoding="utf-8")
    (top / ".hidden.txt").write_text("x", encoding="utf-8")

    (top / "nested").mkdir()
    (top / "nested" / "a.txt").write_text("a", encoding="utf-8")

    (top / ".secret").mkdir()
    (top / ".secret" / "b.txt").write_text("b", encoding="utf-8")

    (top / ".git").mkdir()
    (top / ".git" / "config").write_text("c", encoding="utf-8")

    rows = list(scan_utils.fast_scandir(str(top), include_hidden=False))
    assert rows
    for row in rows:
        assert isinstance(row, tuple)
        assert len(row) == 3
        dirpath, dirs, files = row
        assert isinstance(dirpath, str)
        assert isinstance(dirs, list)
        assert isinstance(files, list)
        for entry in dirs + files:
            assert isinstance(entry, os.DirEntry)

    all_files = {e.path for _d, _dirs, files in rows for e in files}
    all_dirs = {e.name for _d, dirs, _files in rows for e in dirs}

    assert str(top / "visible.txt") in all_files
    assert str(top / ".hidden.txt") not in all_files
    assert "nested" in all_dirs
    assert ".secret" not in all_dirs
    assert ".git" not in all_dirs


def test_fast_scandir_honors_excluded_dirs(tmp_path):
    top = tmp_path / "scan2"
    top.mkdir()
    keep = top / "keep"
    skip = top / "skip"
    keep.mkdir()
    skip.mkdir()
    (keep / "ok.txt").write_text("ok", encoding="utf-8")
    (skip / "no.txt").write_text("no", encoding="utf-8")

    rows = list(
        scan_utils.fast_scandir(
            str(top),
            include_hidden=True,
            excluded_dirs={str(skip.resolve())},
        )
    )
    files = {e.path for _d, _dirs, entries in rows for e in entries}

    assert str(keep / "ok.txt") in files
    assert str(skip / "no.txt") not in files
