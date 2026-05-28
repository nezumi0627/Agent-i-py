"""AgentIClient (WebView) の単体テスト"""
from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

import pytest

from agent_i import AgentIClient, AgentIConfig, AgentSource
from agent_i.exceptions import ApiError, StreamError


class TestAgentIClientInit:
    def test_defaults(self):
        client = AgentIClient()
        assert client.cookies == ""
        assert client.line_version == AgentIConfig.DEFAULT_LINE_VERSION
        assert client.source == AgentSource.CHAT_TAB
        assert client.endpoint == AgentIConfig.DEFAULT_ENDPOINT

    def test_source_as_string(self):
        client = AgentIClient(source="hometab_searchbar")
        assert client.source == AgentSource.HOME_TAB

    def test_history_initially_empty(self):
        assert AgentIClient().history == []


class TestBuildWebviewUrl:
    def setup_method(self):
        self.client = AgentIClient()

    def test_includes_frcode(self):
        url = self.client.build_webview_url()
        assert "fr=line_agenti_chattab_searchbar" in url

    def test_includes_frtype(self):
        url = self.client.build_webview_url()
        assert "frtype=line_chattab_searchbar" in url

    def test_with_query(self):
        url = self.client.build_webview_url("hello")
        assert "q=hello" in url

    def test_without_query(self):
        url = self.client.build_webview_url()
        assert "q=" not in url


class TestMintAnonymousCookies:
    @patch("agent_i.webview.requests.Session.get")
    def test_parses_set_cookie_header(self, mock_get):
        mock_resp = Mock()
        mock_resp.headers.get.return_value = (
            "B=anon-b; Path=/, XB=anon-xb; Path=/"
        )
        mock_get.return_value = mock_resp

        cookies = AgentIClient().mint_anonymous_cookies()

        assert "B=anon-b" in cookies
        assert "XB=anon-xb" in cookies

    @patch("agent_i.webview.requests.Session.get")
    def test_raises_api_error_on_request_exception(self, mock_get):
        import requests as _req
        mock_get.side_effect = _req.RequestException("timeout")

        with pytest.raises(ApiError):
            AgentIClient().mint_anonymous_cookies()


class TestChat:
    def setup_method(self):
        self.client = AgentIClient(cookies="B=dummy")

    def _make_event(self, event_type: str, message: str) -> Mock:
        e = Mock()
        e.event = event_type
        e.data = (
            f'{{"type": "{event_type}", "value": {{"message": "{message}"}}}}'
        )
        return e

    @patch("agent_i.base.requests.Session.request")
    @patch("agent_i.webview.sseclient.SSEClient")
    def test_yields_chunks(self, mock_sse_cls, mock_request):
        mock_request.return_value = Mock()
        mock_sse = Mock()
        mock_sse.events.return_value = [
            self._make_event("compositeMessage-delta", "Hello"),
        ]
        mock_sse_cls.return_value = mock_sse

        chunks = list(self.client.chat("Hi"))

        assert len(chunks) == 1
        assert chunks[0].text == "Hello"

    @patch("agent_i.base.requests.Session.request")
    @patch("agent_i.webview.sseclient.SSEClient")
    def test_appends_to_history(self, mock_sse_cls, mock_request):
        mock_request.return_value = Mock()
        mock_sse = Mock()
        mock_sse.events.return_value = [
            self._make_event("compositeMessage-delta", "World"),
        ]
        mock_sse_cls.return_value = mock_sse

        list(self.client.chat("Hi"))

        assert len(self.client.history) == 2
        assert self.client.history[0].role == "user"
        assert self.client.history[1].role == "assistant"

    @patch("agent_i.base.requests.Session.request")
    @patch("agent_i.webview.sseclient.SSEClient")
    def test_raises_stream_error(self, mock_sse_cls, mock_request):
        mock_request.return_value = Mock()
        mock_sse = Mock()
        mock_sse.events.side_effect = Exception("broken pipe")
        mock_sse_cls.return_value = mock_sse

        with pytest.raises(StreamError):
            list(self.client.chat("Hi"))

    @patch("agent_i.webview.AgentIClient.mint_anonymous_cookies", return_value="B=auto")
    @patch("agent_i.base.requests.Session.request")
    @patch("agent_i.webview.sseclient.SSEClient")
    def test_auto_mints_cookies(self, mock_sse_cls, mock_request, mock_mint):
        client = AgentIClient()  # cookies=""
        mock_request.return_value = Mock()
        mock_sse = Mock()
        mock_sse.events.return_value = []
        mock_sse_cls.return_value = mock_sse

        list(client.chat("Hi"))

        mock_mint.assert_called_once()
        assert client.cookies == "B=auto"


class TestReset:
    @patch("agent_i.base.requests.Session.request")
    @patch("agent_i.webview.sseclient.SSEClient")
    def test_clears_history(self, mock_sse_cls, mock_request):
        client = AgentIClient(cookies="B=x")
        mock_request.return_value = Mock()
        mock_sse = Mock()
        mock_sse.events.return_value = []
        mock_sse_cls.return_value = mock_sse

        list(client.chat("Hello"))
        client.reset()

        assert client.history == []
