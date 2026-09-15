import sys
import types
import unittest
import tempfile
import threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

# Lightweight stubs only if optional UI packages are unavailable in the test runtime.
try:
    import pyfiglet  # noqa
except ImportError:
    mod = types.ModuleType('pyfiglet')
    mod.figlet_format = lambda text, font=None: text
    sys.modules['pyfiglet'] = mod
try:
    import termcolor  # noqa
except ImportError:
    mod = types.ModuleType('termcolor')
    mod.colored = lambda text, color=None: text
    sys.modules['termcolor'] = mod

sys.path.insert(0, str(Path(__file__).parent))
import main


class FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code
        self.closed = False
    def close(self):
        self.closed = True


class LocalHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/ok':
            self.send_response(200)
        elif self.path == '/admin':
            self.send_response(403)
        elif self.path == '/redirect':
            self.send_response(302)
            self.send_header('Location', '/ok')
        else:
            self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        pass


class TotalReconTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), LocalHandler)
        cls.port = cls.server.server_address[1]
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_option1_http_status_normalizes_and_returns_status(self):
        seen = {}
        def fake_get(url, **kwargs):
            seen['url'] = url
            return FakeResponse(204)
        url, status = main.get_http_status('example.test', requester=fake_get)
        self.assertEqual(url, 'http://example.test')
        self.assertEqual(status, 204)
        self.assertEqual(seen['url'], 'http://example.test')

    def test_option1_http_status_rejects_empty(self):
        with self.assertRaises(ValueError):
            main.get_http_status('   ', requester=lambda *a, **k: None)

    def test_option1_http_status_local_integration(self):
        url, status = main.get_http_status(f'127.0.0.1:{self.port}/ok')
        self.assertEqual(url, f'http://127.0.0.1:{self.port}/ok')
        self.assertEqual(status, 200)

    def test_option2_subdomain_scan_collects_only_responders(self):
        def probe(host):
            if host.startswith('www.'):
                return 200, host
            if host.startswith('admin.'):
                return 403, host
            return None
        candidates, results = main.scan_subdomains('https://example.test/', ['www','bad','admin'], 3, probe_fn=probe)
        self.assertEqual(candidates, ['www','bad','admin'])
        self.assertEqual(results, [(403, 'admin.example.test'), (200, 'www.example.test')])

    def test_option2_subdomain_limit_is_bounded(self):
        candidates, _ = main.scan_subdomains('example.test', [str(i) for i in range(6000)], 99999, probe_fn=lambda h: None)
        self.assertEqual(len(candidates), main.MAX_SCAN_LIMIT)

    def test_option2_probe_handles_timeout(self):
        import requests
        def timed_out(*args, **kwargs):
            raise requests.exceptions.Timeout('simulated')
        self.assertIsNone(main._probe_subdomain('example.test', requester=timed_out))

    def test_option3_directory_scan_collects_expected_statuses(self):
        def probe(url):
            if url.endswith('/admin'):
                return 403, url
            if url.endswith('/login'):
                return 200, url
            return None
        candidates, results = main.scan_directories('example.test/', ['/admin','none','login'], 3, probe_fn=probe)
        self.assertEqual(candidates, ['/admin','none','login'])
        self.assertEqual(results, [(403, 'http://example.test/admin'), (200, 'http://example.test/login')])

    def test_option3_directory_limit_is_bounded(self):
        candidates, _ = main.scan_directories('example.test', [str(i) for i in range(6000)], 99999, probe_fn=lambda u: None)
        self.assertEqual(len(candidates), main.MAX_SCAN_LIMIT)

    def test_option3_directory_local_integration(self):
        host = f'127.0.0.1:{self.port}'
        candidates, results = main.scan_directories(host, ['ok', 'admin', 'missing', 'redirect'], 4)
        self.assertEqual(candidates, ['ok', 'admin', 'missing', 'redirect'])
        self.assertIn((200, f'http://{host}/ok'), results)
        self.assertIn((403, f'http://{host}/admin'), results)
        self.assertIn((302, f'http://{host}/redirect'), results)
        self.assertNotIn((404, f'http://{host}/missing'), results)

    def test_option3_probe_handles_timeout(self):
        import requests
        def timed_out(*args, **kwargs):
            raise requests.exceptions.Timeout('simulated')
        self.assertIsNone(main._probe_directory('http://example.test/admin', requester=timed_out))

    def test_option4_google_dork_urls_are_encoded_and_limited(self):
        urls = main.build_google_dork_urls('https://example.test/', ['inurl:admin', 'filetype:pdf'], 1)
        self.assertEqual(len(urls), 1)
        decoded = unquote(urls[0])
        self.assertIn('site:example.test inurl:admin', decoded)
        self.assertTrue(urls[0].startswith('https://www.google.com/search?q='))

    def test_option5_jwt_finds_secret(self):
        token = main.jwt.encode({'user':'tester'}, 'correct-secret', algorithm='HS256')
        found = main.find_jwt_secret(token, 'HS256', ['wrong\n', 'correct-secret\n', 'later\n'])
        self.assertEqual(found, 'correct-secret')

    def test_option5_jwt_returns_none_when_not_found(self):
        token = main.jwt.encode({'user':'tester'}, 'correct-secret', algorithm='HS256')
        found = main.find_jwt_secret(token, 'HS256', ['wrong1\n', 'wrong2\n'])
        self.assertIsNone(found)

    def test_normalize_host(self):
        self.assertEqual(main._normalize_host(' https://example.test/ '), 'example.test')

    def test_popup_metrics_short_message_uses_compact_layout(self):
        width, height, scrollable = main._popup_metrics("Operation completed successfully.")
        self.assertFalse(scrollable)
        self.assertGreaterEqual(width, 360)
        self.assertGreaterEqual(height, 180)

    def test_popup_metrics_long_results_use_scrollable_layout(self):
        text = "\n".join(f"200 - host-{i}.example.test" for i in range(40))
        width, height, scrollable = main._popup_metrics(text)
        self.assertTrue(scrollable)
        self.assertLessEqual(width, 900)
        self.assertLessEqual(height, 680)

    def test_popup_metrics_handles_single_very_long_line(self):
        width, height, scrollable = main._popup_metrics("x" * 500)
        self.assertTrue(scrollable)
        self.assertLessEqual(width, 900)

    def test_wordlist_reader_honors_limit(self):
        old_base = main.BASE_DIR
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / 'sample.txt').write_text('one\n\ntwo\nthree\nfour\n', encoding='utf-8')
            main.BASE_DIR = tmp_path
            try:
                self.assertEqual(main._read_lines('sample.txt', limit=2), ['one', 'two'])
            finally:
                main.BASE_DIR = old_base


if __name__ == '__main__':
    unittest.main(verbosity=2)
