"""Tests for web_fetch tool — with mocked HTTP requests."""

import pytest
from unittest.mock import patch, MagicMock
from flexygent.tools.web import web_fetch, MAX_LENGTH


class TestWebFetch:
    def test_no_url_returns_error(self):
        result = web_fetch({})
        assert "Error" in result

    def test_successful_fetch(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><p>Hello World</p></body></html>"

        with patch("flexygent.tools.web.requests.get", return_value=mock_response):
            result = web_fetch({"url": "https://example.com"})
        assert "Hello World" in result

    def test_strips_script_tags(self):
        html = "<html><body><script>alert('x')</script><p>Content</p></body></html>"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = html

        with patch("flexygent.tools.web.requests.get", return_value=mock_response):
            result = web_fetch({"url": "https://example.com"})
        assert "alert" not in result
        assert "Content" in result

    def test_strips_nav_footer_header(self):
        html = """
        <html><body>
            <header>Header Content</header>
            <nav>Nav Links</nav>
            <p>Main Content</p>
            <footer>Footer Content</footer>
        </body></html>
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = html

        with patch("flexygent.tools.web.requests.get", return_value=mock_response):
            result = web_fetch({"url": "https://example.com"})
        assert "Main Content" in result
        assert "Header Content" not in result
        assert "Nav Links" not in result
        assert "Footer Content" not in result

    def test_truncation_on_long_content(self):
        long_content = "<html><body><p>" + "x" * 10000 + "</p></body></html>"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = long_content

        with patch("flexygent.tools.web.requests.get", return_value=mock_response):
            result = web_fetch({"url": "https://example.com"})
        assert "truncated" in result
        assert len(result) > MAX_LENGTH  # includes truncation message

    def test_non_200_returns_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("flexygent.tools.web.requests.get", return_value=mock_response):
            result = web_fetch({"url": "https://example.com/404"})
        assert "Error" in result
        assert "not reachable" in result

    def test_network_error(self):
        with patch("flexygent.tools.web.requests.get", side_effect=ConnectionError("timeout")):
            result = web_fetch({"url": "https://example.com"})
        assert "Error" in result
