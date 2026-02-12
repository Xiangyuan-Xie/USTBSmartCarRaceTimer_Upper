import unittest
from unittest.mock import patch

from core.web_server import WebServer


class TestWebServer(unittest.TestCase):
    def setUp(self):
        # Reset singleton
        if WebServer._instance:
            WebServer._instance = None

    @patch("core.web_server.os.makedirs")
    @patch("core.web_server.FastAPI")
    @patch("core.web_server.StaticFiles")
    @patch("core.web_server.Jinja2Templates")
    def test_initialization(self, mock_templates, mock_static, mock_fastapi, mock_makedirs):
        server = WebServer()

        self.assertTrue(server._initialized)
        mock_fastapi.assert_called_once()

        # Check directories creation
        self.assertTrue(mock_makedirs.called)

        # Check mounting
        server.app.mount.assert_called()

    @patch("core.web_server.Thread")
    def test_start(self, mock_thread):
        server = WebServer()
        server.start()
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()

    def test_singleton(self):
        s1 = WebServer()
        s2 = WebServer()
        self.assertIs(s1, s2)
