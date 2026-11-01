import tempfile
from pathlib import Path

from django.test import SimpleTestCase, override_settings


class FrontendServingTests(SimpleTestCase):
    """config/frontend.py: Django가 Flutter Web 빌드를 서빙 (ngrok 공개용)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.build = Path(self._tmp.name)
        (self.build / "index.html").write_text("<html>app</html>", encoding="utf-8")
        (self.build / "assets").mkdir()
        (self.build / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
        self.addCleanup(self._tmp.cleanup)

    def _get(self, url):
        with override_settings(FRONTEND_BUILD_DIR=self.build):
            return self.client.get(url)

    def test_root_serves_index(self):
        res = self._get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"app", b"".join(res.streaming_content))

    def test_static_file_is_served(self):
        res = self._get("/assets/app.js")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"console.log", b"".join(res.streaming_content))

    def test_unknown_path_falls_back_to_index(self):
        res = self._get("/some/route")
        self.assertIn(b"app", b"".join(res.streaming_content))

    def test_path_traversal_does_not_escape_build_dir(self):
        res = self._get("/..%2F..%2Fsettings.py")
        self.assertIn(b"app", b"".join(res.streaming_content))

    def test_api_paths_are_not_captured(self):
        res = self._get("/api/auth/google/")
        self.assertEqual(res["Content-Type"], "application/json")

    def test_missing_build_returns_404(self):
        with override_settings(FRONTEND_BUILD_DIR=self.build / "missing"):
            res = self.client.get("/")
        self.assertEqual(res.status_code, 404)

    def test_coop_allows_google_sign_in_popup(self):
        res = self._get("/")
        res.close()  # 파일 핸들을 닫아야 Windows에서 임시 폴더가 지워진다
        self.assertEqual(res["Cross-Origin-Opener-Policy"], "same-origin-allow-popups")
