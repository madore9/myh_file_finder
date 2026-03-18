import large_file_finder as lff
import update_checker


def test_batching_constants_are_present_and_positive():
    assert lff.ScannerThread.BATCH_INTERVAL > 0
    assert lff.ScannerThread.BATCH_MAX_SIZE >= 1
    assert lff.StringSearchThread.BATCH_INTERVAL > 0
    assert lff.StringSearchThread.BATCH_MAX_SIZE >= 1
    assert lff.SENSITIVE_FINDING_BATCH_SIZE >= 1
    assert lff.MDLS_BATCH_SIZE >= 1


def test_signal_attributes_exist_without_gui_instantiation():
    for cls, names in [
        (lff.ScannerThread, ["file_found", "files_found_batch", "scan_progress", "scan_finished", "scan_error"]),
        (lff.SensitiveScannerThread, ["finding_batch_ready", "scan_progress", "scan_finished", "scan_error"]),
        (lff.StringSearchThread, ["match_found", "matches_found_batch", "scan_progress", "scan_finished", "scan_error"]),
        (lff.LastOpenedFetcher, ["result_ready", "fetch_finished"]),
        (update_checker.UpdateCheckerThread, ["update_available", "no_update", "check_failed"]),
    ]:
        for name in names:
            assert hasattr(cls, name)


def test_thread_request_stop_flags():
    scanner = lff.ScannerThread(scan_path=".", min_size_bytes=1, include_hidden=True)
    sensitive = lff.SensitiveScannerThread(scan_path=".", active_profiles=[])
    search = lff.StringSearchThread(search_string="x", use_regex=False, scan_path=".", include_hidden=True)
    fetcher = lff.LastOpenedFetcher(file_paths=[])

    for obj in [scanner, sensitive, search, fetcher]:
        assert getattr(obj, "_stop_requested", False) is False
        obj.request_stop()
        assert obj._stop_requested is True
