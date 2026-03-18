import os
import subprocess
from datetime import datetime, timedelta

import large_file_finder as lff


class _Proc:
    def __init__(self, stdout):
        self.stdout = stdout


def test_format_size_boundaries():
    assert lff.format_size(100) == "100 B"
    assert lff.format_size(1024) == "1.0 KB"
    assert lff.format_size(1536) == "1.5 KB"
    assert lff.format_size(1024**2) == "1.0 MB"
    assert lff.format_size(1024**3) == "1.00 GB"


def test_get_app_bundle_root_detects_mac_bundle(monkeypatch, tmp_path):
    exe = tmp_path / "MyTool.app" / "Contents" / "MacOS" / "mytool"
    exe.parent.mkdir(parents=True)
    exe.write_text("x", encoding="utf-8")

    monkeypatch.setattr(lff.sys, "executable", str(exe))
    assert lff.get_app_bundle_root().endswith("MyTool.app")


def test_get_app_bundle_root_non_bundle(monkeypatch, tmp_path):
    exe = tmp_path / "python"
    exe.write_text("x", encoding="utf-8")
    monkeypatch.setattr(lff.sys, "executable", str(exe))
    assert lff.get_app_bundle_root() is None


def test_get_last_opened_parsing(monkeypatch):
    raw = "2024-01-15 10:30:00 +0000\n"
    monkeypatch.setattr(
        lff.subprocess,
        "run",
        lambda *a, **k: _Proc(stdout=raw),
    )
    out = lff.get_last_opened("/tmp/f")
    assert out == "2024-01-15 10:30 AM"


def test_get_last_opened_null_and_error(monkeypatch):
    monkeypatch.setattr(lff.subprocess, "run", lambda *a, **k: _Proc(stdout="(null)\n"))
    assert lff.get_last_opened("/tmp/f") == "Never / Unknown"

    def raise_err(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(lff.subprocess, "run", raise_err)
    assert lff.get_last_opened("/tmp/f") == "N/A"


def test_file_analyzer_extension_and_days_parsing():
    assert lff.FileAnalyzer._get_extension("x.tar.gz") == ".tar.gz"
    assert lff.FileAnalyzer._get_extension("x.TXT") == ".txt"
    assert lff.FileAnalyzer.parse_last_opened_to_days("Never / Unknown") == 999999
    assert lff.FileAnalyzer.parse_last_opened_to_days("N/A") is None


def test_file_analyzer_analyze_recent_vs_old():
    old = (datetime.now() - timedelta(days=800)).strftime("%Y-%m-%d %I:%M %p")
    recent = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %I:%M %p")

    old_score, _old_label, old_reason = lff.FileAnalyzer.analyze("/Users/me/Downloads/file.tmp", 1024, old)
    recent_score, _recent_label, recent_reason = lff.FileAnalyzer.analyze("/Users/me/file.tmp", 1024, recent)

    assert old_score > recent_score
    assert isinstance(old_reason, str)
    assert isinstance(recent_reason, str)


def test_file_analyzer_labels_likely_safe_review_keep():
    safe_score, safe_label, _ = lff.FileAnalyzer.analyze("/Users/me/.Trash/file.tmp", 1024, "Never / Unknown")
    review_score, review_label, _ = lff.FileAnalyzer.analyze("/Users/me/docs/file.img", 1024, None)
    keep_score, keep_label, _ = lff.FileAnalyzer.analyze(
        "/System/Library/photo.jpg",
        1024,
        (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %I:%M %p"),
    )

    assert safe_score >= 65 and "Likely Safe" in safe_label
    assert 40 <= review_score < 65 and "Review" in review_label
    assert keep_score < 40 and "Keep" in keep_label


def test_size_table_item_comparison_sorting():
    items = [
        lff.SizeTableItem("10 MB", 10),
        lff.SizeTableItem("1 MB", 1),
        lff.SizeTableItem("5 MB", 5),
    ]
    sorted_items = sorted(items)
    assert [i._sort_value for i in sorted_items] == [1, 5, 10]


def test_hash_helpers_and_inode_uniqueness(tmp_path):
    f1 = tmp_path / "a.bin"
    f2 = tmp_path / "b.bin"
    f1.write_bytes(b"abcdef" * 2000)
    f2.write_bytes(b"abcdef" * 2000)

    assert lff._file_quick_hash(str(f1)) == lff._file_quick_hash(str(f2))
    assert lff._file_content_hash(str(f1), f1.stat().st_size) == lff._file_content_hash(str(f2), f2.stat().st_size)

    link = tmp_path / "a_link.bin"
    os.link(f1, link)
    uniq = lff._unique_paths_by_inode([str(f1), str(link), str(f2)])
    assert len(uniq) == 2


def test_batch_get_last_opened_parses_lines(monkeypatch):
    out = "\n".join(
        [
            "kMDItemLastUsedDate = 2024-02-01 12:30:00 +0000",
            "kMDItemLastUsedDate = (null)",
            "kMDItemLastUsedDate = invalid",
        ]
    )
    monkeypatch.setattr(lff.subprocess, "run", lambda *a, **k: _Proc(stdout=out))

    files = ["/tmp/one", "/tmp/two", "/tmp/three"]
    result = lff._batch_get_last_opened(files)

    assert result["/tmp/one"] == "2024-02-01 12:30 PM"
    assert result["/tmp/two"] == "Never / Unknown"
    assert result["/tmp/three"] == "N/A"


def test_batch_get_last_opened_timeout_marks_na(monkeypatch):
    def raise_timeout(*_a, **_k):
        raise subprocess.TimeoutExpired(cmd="mdls", timeout=30)

    monkeypatch.setattr(lff.subprocess, "run", raise_timeout)
    files = ["/tmp/a", "/tmp/b"]
    result = lff._batch_get_last_opened(files)
    assert result == {"/tmp/a": "N/A", "/tmp/b": "N/A"}
