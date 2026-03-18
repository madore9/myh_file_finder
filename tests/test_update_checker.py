import json
import ssl
import sys
import urllib.error

import update_checker


class _DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_parse_version_expected_and_edge_cases():
    assert update_checker.parse_version("v1.2.3") == (1, 2, 3)
    assert update_checker.parse_version("1.2.3") == (1, 2, 3)
    assert update_checker.parse_version("1.0") == (1, 0)
    assert update_checker.parse_version("3.beta.2") == (3, 0, 2)
    assert update_checker.parse_version("v") == (0,)
    assert update_checker.parse_version("") == (0,)


def test_get_app_version_reads_local_version(monkeypatch, tmp_path):
    module_dir = tmp_path / "app"
    module_dir.mkdir()
    (module_dir / "VERSION").write_text("7.8.9\n", encoding="utf-8")

    monkeypatch.setattr(update_checker, "__file__", str(module_dir / "update_checker.py"))
    monkeypatch.setattr(sys, "executable", str(tmp_path / "python"))

    assert update_checker.get_app_version() == "7.8.9"


def test_get_app_version_falls_back_to_default(monkeypatch, tmp_path):
    monkeypatch.setattr(update_checker, "__file__", str(tmp_path / "missing" / "update_checker.py"))
    monkeypatch.setattr(sys, "executable", str(tmp_path / "missing" / "python"))
    assert update_checker.get_app_version() == "0.0.0"


def test_update_thread_emits_update_available(monkeypatch):
    payload = {
        "tag_name": "v9.9.9",
        "html_url": "https://example.test/release",
        "body": "notes",
    }

    def fake_urlopen(req, timeout=None, context=None):
        assert req.full_url == update_checker.API_URL
        assert timeout == update_checker.REQUEST_TIMEOUT
        assert context is not None
        return _DummyResponse(json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr(update_checker.urllib.request, "urlopen", fake_urlopen)

    thread = update_checker.UpdateCheckerThread("1.0.0")
    got = []
    thread.update_available.connect(lambda v, u, c: got.append((v, u, c)))
    thread.no_update.connect(lambda: got.append(("no", "", "")))
    thread.check_failed.connect(lambda e: got.append(("err", e, "")))

    thread.run()

    assert got == [("9.9.9", "https://example.test/release", "notes")]


def test_update_thread_configures_ssl_context_for_unverified_connection(monkeypatch):
    payload = {"tag_name": "v1.0.0", "html_url": "https://example.test/release", "body": ""}

    class _Ctx:
        def __init__(self):
            self.check_hostname = True
            self.verify_mode = "initial"

    seen = {}

    def fake_create_default_context():
        ctx = _Ctx()
        seen["ctx"] = ctx
        return ctx

    def fake_urlopen(req, timeout=None, context=None):
        assert context is seen["ctx"]
        return _DummyResponse(json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr(ssl, "create_default_context", fake_create_default_context)
    monkeypatch.setattr(update_checker.urllib.request, "urlopen", fake_urlopen)

    thread = update_checker.UpdateCheckerThread("1.0.0")
    thread.run()

    assert seen["ctx"].check_hostname is False
    assert seen["ctx"].verify_mode == ssl.CERT_NONE


def test_update_thread_emits_no_update(monkeypatch):
    payload = {"tag_name": "v1.0.0", "html_url": "https://example.test/release", "body": ""}
    monkeypatch.setattr(
        update_checker.urllib.request,
        "urlopen",
        lambda req, timeout=None, context=None: _DummyResponse(json.dumps(payload).encode("utf-8")),
    )

    thread = update_checker.UpdateCheckerThread("1.0.0")
    flags = {"no": 0, "err": 0, "upd": 0}
    thread.no_update.connect(lambda: flags.__setitem__("no", flags["no"] + 1))
    thread.check_failed.connect(lambda _e: flags.__setitem__("err", flags["err"] + 1))
    thread.update_available.connect(lambda *_: flags.__setitem__("upd", flags["upd"] + 1))

    thread.run()
    assert flags == {"no": 1, "err": 0, "upd": 0}


def test_update_thread_http_error(monkeypatch):
    def raise_http(*_args, **_kwargs):
        raise urllib.error.HTTPError(update_checker.API_URL, 500, "boom", None, None)

    monkeypatch.setattr(update_checker.urllib.request, "urlopen", raise_http)

    thread = update_checker.UpdateCheckerThread("1.0.0")
    errors = []
    thread.check_failed.connect(errors.append)
    thread.run()

    assert errors and errors[0].startswith("HTTP 500")


def test_update_thread_url_error(monkeypatch):
    monkeypatch.setattr(
        update_checker.urllib.request,
        "urlopen",
        lambda *_a, **_k: (_ for _ in ()).throw(urllib.error.URLError("offline")),
    )

    thread = update_checker.UpdateCheckerThread("1.0.0")
    errors = []
    thread.check_failed.connect(errors.append)
    thread.run()

    assert errors and "Network error" in errors[0]


def test_update_thread_parse_error(monkeypatch):
    monkeypatch.setattr(
        update_checker.urllib.request,
        "urlopen",
        lambda *_a, **_k: _DummyResponse(b"not-json"),
    )

    thread = update_checker.UpdateCheckerThread("1.0.0")
    errors = []
    thread.check_failed.connect(errors.append)
    thread.run()

    assert errors and errors[0].startswith("Parse error:")
