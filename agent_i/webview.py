"""Agent I (WebView) クライアント"""
from __future__ import annotations

import uuid
from typing import Dict, Generator, List, Optional

import requests
import sseclient

from .base import BaseApiClient
from .config import AgentIConfig, AgentSource
from .exceptions import ApiError, StreamError
from .models import AgentIChunk, ChatMessage


class AgentIClient(BaseApiClient):
    """WebViewパス用LINE Agent I クライアント

    search.yahoo.co.jp経由のWebView Agent Iを使用
    Yahooの匿名クッキーを自動的に取得・使用
    """

    def __init__(
        self,
        cookies: str = "",
        line_version: str = AgentIConfig.DEFAULT_LINE_VERSION,
        source: AgentSource | str = AgentIConfig.DEFAULT_SOURCE,
        endpoint: str = AgentIConfig.DEFAULT_ENDPOINT,
        timeout: int = 30
    ) -> None:
        """
        Args:
            cookies: Yahooクッキー文字列（省略時は自動取得）
            line_version: LINEアプリバージョン
            source: Agent I呼び出し元
            endpoint: SSEエンドポイントURL
            timeout: リクエストタイムアウト
        """
        super().__init__(timeout=timeout)
        self.cookies = cookies
        self.line_version = line_version
        self.source = AgentSource(source) if isinstance(source, str) else source
        self.endpoint = endpoint
        self._history: List[ChatMessage] = []

    def build_webview_url(self, query: Optional[str] = None) -> str:
        """LINE AndroidがWebViewで読み込むURLを構築"""
        params = {
            "fr": self.source.frcode,
            "frtype": self.source.frtype
        }
        if query:
            params["q"] = query

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{AgentIConfig.WEBVIEW_BASE_URL}?{query_string}"

    def mint_anonymous_cookies(self) -> str:
        """匿名Yahooクッキーを取得"""
        url = self.build_webview_url()
        try:
            response = self.session.get(url, allow_redirects=True, timeout=self.timeout)
            set_cookie = response.headers.get("set-cookie", "")
            
            cookies = []
            for cookie_line in set_cookie.split(','):
                if '=' in cookie_line:
                    cookie = cookie_line.split(';')[0].strip()
                    if cookie:
                        cookies.append(cookie)
            
            return "; ".join(cookies)
        except requests.RequestException as e:
            raise ApiError(f"Failed to fetch cookies: {str(e)}", status_code=0) from e

    @staticmethod
    def _random_id() -> str:
        """32文字の16進IDを生成"""
        return uuid.uuid4().hex

    def chat(self, user_text: str, extra: Optional[Dict[str, str]] = None) -> Generator[AgentIChunk, None, None]:
        """メッセージを送信し、SSEチャンクをジェネレート"""
        if not self.cookies:
            self.cookies = self.mint_anonymous_cookies()

        user_msg = ChatMessage(
            id=self._random_id(),
            role="user",
            contents=[{"type": "text", "text": user_text}]
        )
        self._history.append(user_msg)

        extra = extra or {}
        body = {
            "chats": [{"id": msg.id, "role": msg.role, "contents": msg.contents} for msg in self._history],
            "context": {
                "agentMode": "multi",
                "logid": extra.get("logid", self._random_id()),
                "qId": extra.get("qId", self._random_id()),
                "snc": True,
                "frtype": self.source.frtype,
                "frcode": self.source.frcode,
                "requestType": "free_text",
                "index": 0,
                "yz": False,
                "pdis": False,
            },
            "debug": {}
        }

        headers = {
            "user-agent": f"Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Line/{self.line_version}/Agenti",
            "accept": "text/event-stream",
            "content-type": "application/json",
            "pragma": "no-cache",
            "cache-control": "no-cache",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "accept-language": "ja",
            "origin": "https://search.yahoo.co.jp",
            "referer": "https://search.yahoo.co.jp/",
            "priority": "u=3, i",
            "cookie": self.cookies
        }

        response = self._request("POST", self.endpoint, headers=headers, json_data=body, stream=True)

        assistant_text_parts: List[str] = []
        try:
            client = sseclient.SSEClient(response)
            for event in client.events():
                chunk = AgentIChunk.from_sse_event(event.data, event.event)
                if chunk:
                    if chunk.text:
                        assistant_text_parts.append(chunk.text)
                    yield chunk
        except Exception as e:
            raise StreamError(f"Error parsing SSE stream: {str(e)}") from e

        if assistant_text_parts:
            assistant_turn = ChatMessage(
                id=self._random_id(),
                role="assistant",
                contents=[{"type": "text", "text": "".join(assistant_text_parts)}]
            )
            self._history.append(assistant_turn)

    def reset(self) -> None:
        """会話履歴をクリア"""
        self._history.clear()

    @property
    def history(self) -> List[ChatMessage]:
        """読み取り専用の会話履歴"""
        return self._history.copy()
