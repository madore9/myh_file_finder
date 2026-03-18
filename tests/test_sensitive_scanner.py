import sensitive_scanner


def test_mask_value_profiles():
    assert sensitive_scanner.mask_value("123-45-6789", "SSN") == "***-**-6789"
    assert sensitive_scanner.mask_value("123456789", "SSN") == "*****6789"
    assert sensitive_scanner.mask_value("12345678", "HUID") == "12****78"
    assert sensitive_scanner.mask_value("12-3456789", "TAX") == "12-*****89"
    assert sensitive_scanner.mask_value("john.doe@harvard.edu", "EMAIL").endswith("@harvard.edu")


def test_compute_confidence_increases_with_context_and_matches():
    content = " ".join(["student", "harvard", "transcript", "grade", "gpa", "registrar"]).lower()
    high = sensitive_scanner.compute_confidence("HUID", "student_roster.csv", content, 12, ".csv")
    low = sensitive_scanner.compute_confidence("HUID", "notes.txt", "random text", 1, ".txt")
    assert high == "HIGH"
    assert low in {"LOW", "MEDIUM"}


def test_should_skip_dir_hidden_and_excluded(tmp_path):
    hidden = tmp_path / ".secret"
    hidden.mkdir()
    blocked = tmp_path / "blocked"
    blocked.mkdir()

    assert sensitive_scanner.should_skip_dir(".secret", str(hidden), include_hidden=False)
    assert not sensitive_scanner.should_skip_dir(".secret", str(hidden), include_hidden=True)
    assert sensitive_scanner.should_skip_dir("blocked", str(blocked), excluded_dirs={str(blocked.resolve())})


def test_scan_file_detects_huid_ssn_tax_and_email(tmp_path):
    f = tmp_path / "sensitive.txt"
    f.write_text(
        "\n".join(
            [
                "huid 12345678",
                "ssn 123-45-6789",
                "ein 12-3456789",
                "email jane_doe@harvard.edu",
            ]
        ),
        encoding="utf-8",
    )

    results = sensitive_scanner.scan_file(str(f), ["HUID", "SSN", "TAX", "EMAIL"])
    by_profile = {r["profile"]: r for r in results}

    assert {"HUID", "SSN", "TAX", "EMAIL"}.issubset(set(by_profile))
    assert "12345678" in by_profile["HUID"]["unique_values"]
    assert "123-45-6789" in by_profile["SSN"]["unique_values"]
    assert "12-3456789" in by_profile["TAX"]["unique_values"]
    assert "jane_doe@harvard.edu" in by_profile["EMAIL"]["unique_values"]


def test_scan_file_ignores_repeated_digit_huid(tmp_path):
    f = tmp_path / "huid.txt"
    f.write_text("11111111\n", encoding="utf-8")
    results = sensitive_scanner.scan_file(str(f), ["HUID"])
    assert results == []


def test_scan_file_binary_like_content_returns_empty(tmp_path):
    f = tmp_path / "blob.bin"
    f.write_bytes(b"\x00\xff\x00\x10\x80\x90")
    assert sensitive_scanner.scan_file(str(f), ["HUID", "SSN", "TAX", "EMAIL"]) == []


def test_scan_file_respects_max_file_size(tmp_path, monkeypatch):
    f = tmp_path / "large.txt"
    f.write_text("ssn 123-45-6789\n", encoding="utf-8")
    monkeypatch.setattr(sensitive_scanner, "MAX_FILE_SIZE", 1)
    assert sensitive_scanner.scan_file(str(f), ["SSN"]) == []


def test_secure_delete_function_exists():
    assert hasattr(sensitive_scanner, "secure_delete_file")
    assert callable(sensitive_scanner.secure_delete_file)


def test_secure_delete_file_removes_file(tmp_path):
    f = tmp_path / "secret.txt"
    f.write_text("sensitive", encoding="utf-8")
    ok = sensitive_scanner.secure_delete_file(str(f), passes=1)
    assert ok is True
    assert not f.exists()
