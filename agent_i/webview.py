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
    """WebView パス用 LINE Agent I クライアント。

    ``search.yahoo.co.jp`` 経由の WebView Agent I を使用します。
    Yahoo の匿名クッキーを初回リクエスト時に自動取得します。

    Args:
        cookies: Yahoo クッキー文字列。省略時は :meth:`mint_anonymous_cookies` で自動取得。
        line_version: LINE アプリバージョン文字列。
        source: Agent I 呼び出し元ソース種別。
        endpoint: SSE エンドポイント URL。
        timeout: リクエストタイムアウト秒数。

    Example::

        client = AgentIClient()
        for chunk in client.chat("こんにちは"):
            if chunk.text:
                print(chunk.text, end="", flush=True)
    """

    def __init__(
        self,
        cookies: str = "",
        line_version: str = AgentIConfig.DEFAULT_LINE_VERSION,
        source: AgentSource | str = AgentIConfig.DEFAULT_SOURCE,
        endpoint: str = AgentIConfig.DEFAULT_ENDPOINT,
        timeout: int = 30,
    ) -> None:
        super().__init__(timeout=timeout)
        self.cookies = cookies
        self.line_version = line_version
        self.source = AgentSource(source) if isinstance(source, str) else source
        self.endpoint = endpoint
        self._history: List[ChatMessage] = []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _new_id() -> str:
        """32 文字の 16 進 ID を生成する"""
        return uuid.uuid4().hex

    def _chat_headers(self) -> Dict[str, str]:
        """チャットリクエスト用ヘッダーを構築する"""
        return {
            "user-agent": (
                f"Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) "
                f"AppleWebKit/605.1.15 (KHTML, like Gecko) Line/{self.line_version}/Agenti"
            ),
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
            "cookie": self.cookies,
        }

    def _build_body(
        self, extra: Optional[Dict[str, str]] = None
    ) -> Dict:
        """チャットリクエストボディを組み立てる"""
        extra = extra or {}
        return {
            "chats": [msg.to_dict() for msg in self._history],
            "context": {
                "agentMode": "multi",
                "logid": extra.get("logid", self._new_id()),
                "qId": extra.get("qId", self._new_id()),
                "snc": True,
                "frtype": self.source.frtype,
                "frcode": self.source.frcode,
                "requestType": "free_text",
                "index": 0,
                "yz": False,
                "pdis": False,
            },
            "debug": {},
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_webview_url(self, query: Optional[str] = None) -> str:
        """LINE Android が WebView で読み込む URL を構築する"""
        params = {
            "fr": self.source.frcode,
            "frtype": self.source.frtype,
        }
        if query:
            params["q"] = query
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{AgentIConfig.WEBVIEW_BASE_URL}?{qs}"

    def mint_anonymous_cookies(self) -> str:
        """匿名 Yahoo クッキーを取得する。

        Returns:
            セミコロン区切りのクッキー文字列。

        Raises:
            :class:`ApiError`: クッキー取得リクエストが失敗した場合。
        """
        url = self.build_webview_url()
        try:
            response = self.session.get(url, allow_redirects=True, timeout=self.timeout)
            raw_set_cookie = response.headers.get("set-cookie", "")
            cookies = [
                part.split(";")[0].strip()
                for part in raw_set_cookie.split(",")
                if "=" in part
            ]
            return "; ".join(filter(None, cookies))
        except requests.RequestException as exc:
            raise ApiError(
                f"Failed to fetch anonymous cookies: {exc}", status_code=0
            ) from exc

    def chat(
        self,
        user_text: str,
        extra: Optional[Dict[str, str]] = None,
    ) -> Generator[AgentIChunk, None, None]:
        """メッセージを送信し、SSE チャンクをジェネレートする。

        初回呼び出し時にクッキーが未設定であれば自動取得します。

        Args:
            user_text: ユーザーからのメッセージテキスト。
            extra: context フィールドに追加する任意パラメータ（``logid``, ``qId`` など）。

        Yields:
            :class:`AgentIChunk` — 各 SSE イベントのチャンク。

        Raises:
            :class:`StreamError`: SSE ストリームの解析に失敗した場合。
        """
        if not self.cookies:
            self.cookies = self.mint_anonymous_cookies()

        self._history.append(
            ChatMessage(
                id=self._new_id(),
                role="user",
                contents=[{"type": "text", "text": user_text}],
            )
        )

        response = self._request(
            "POST",
            self.endpoint,
            headers=self._chat_headers(),
            json_data=self._build_body(extra),
            stream=True,
        )

        assistant_parts: List[str] = []
        try:
            for event in sseclient.SSEClient(response).events():
                chunk = AgentIChunk.from_sse_event(event.data, event.event)
                if chunk:
                    if chunk.text:
                        assistant_parts.append(chunk.text)
                    yield chunk
        except Exception as exc:
            raise StreamError(f"SSE stream error: {exc}") from exc

        if assistant_parts:
            self._history.append(
                ChatMessage(
                    id=self._new_id(),
                    role="assistant",
                    contents=[{"type": "text", "text": "".join(assistant_parts)}],
                )
            )

    def reset(self) -> None:
        """会話履歴をクリアする"""
        self._history.clear()

    @property
    def history(self) -> List[ChatMessage]:
        """読み取り専用の会話履歴"""
        return list(self._history)
