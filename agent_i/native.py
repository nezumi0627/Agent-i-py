"""ネイティブ LINE AI クライアント"""
from __future__ import annotations

from typing import Dict, Generator, Optional

import requests
import sseclient

from .base import BaseApiClient
from .config import ContextType, LineAiConfig
from .exceptions import StreamError
from .models import LineAiQueryChunk, LineAiResponse


class LineAiClient(BaseApiClient):
    """ネイティブ LINE AI クライアント。

    ``com.linecorp.line.lineai.impl.ui.LineAiActivity`` で使用される
    ネイティブ LINE AI API のラッパーです。

    Args:
        access_token: LINE AI チャネルトークン（HAR 等から抽出した ``X-Access-Token`` 値）。
        line_version: LINE アプリのバージョン文字列。
        line_os: LINE アプリの OS 種別文字列（例: ``"IOS"``, ``"ANDROID"``）。
        host: API ホスト URL。デフォルトは本番ホスト。
        accept_language: ``Accept-Language`` ヘッダー値。
        timeout: リクエストタイムアウト秒数。

    Example::

        client = LineAiClient(access_token="YOUR_TOKEN")
        client.submit_agreement()
        res = client.create_thread()
        thread_id = res.body["result"]["threadId"]
        for chunk in client.query(thread_id=thread_id, message="Hello"):
            print(chunk.data)
    """

    def __init__(
        self,
        access_token: str,
        line_version: str = LineAiConfig.DEFAULT_LINE_VERSION,
        line_os: str = LineAiConfig.DEFAULT_LINE_OS,
        host: str = LineAiConfig.DEFAULT_HOST,
        accept_language: str = LineAiConfig.DEFAULT_ACCEPT_LANGUAGE,
        timeout: int = 30,
    ) -> None:
        super().__init__(timeout=timeout)
        self.access_token = access_token
        self.line_version = line_version
        self.line_os = line_os
        self.host = host.rstrip("/")
        self.accept_language = accept_language

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """共通リクエストヘッダーを構築する"""
        headers: Dict[str, str] = {
            "accept": "application/json",
            "user-agent": (
                f"LINE/{self.line_version} CFNetwork/3860.200.71 Darwin/25.1.0"
            ),
            "x-access-token": self.access_token,
            "x-line-version": self.line_version,
            "x-line-os": self.line_os,
            "accept-language": self.accept_language,
        }
        if extra:
            headers.update(extra)
        return headers

    def _json_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """JSON ボディを送信する場合のヘッダー"""
        return self._headers({"content-type": "application/json; charset=utf-8", **(extra or {})})

    # ------------------------------------------------------------------
    # API endpoints
    # ------------------------------------------------------------------

    def get_service_info(self) -> LineAiResponse:
        """``GET /v2/service-info`` — AI サービス一覧を取得する"""
        return self.get(f"{self.host}/v2/service-info", headers=self._headers())

    def get_prompt_presets(
        self,
        context_type: ContextType | str,
        accept_language: Optional[str] = None,
    ) -> LineAiResponse:
        """``GET /v2/{contextType}/prompt-preset`` — プロンプトプリセット一覧を取得する"""
        ctx = (
            ContextType(context_type).value
            if isinstance(context_type, str)
            else context_type.value
        )
        extra = {"accept-language": accept_language} if accept_language else None
        return self.get(
            f"{self.host}/v2/{ctx}/prompt-preset", headers=self._headers(extra)
        )

    def submit_agreement(self) -> LineAiResponse:
        """``POST /v2/user/agreement`` — 利用規約に同意する"""
        return self.post(
            f"{self.host}/v2/user/agreement", headers=self._json_headers(), data=""
        )

    def create_thread(self) -> LineAiResponse:
        """``POST /v2/thread`` — 新しいスレッドを作成する"""
        return self.post(
            f"{self.host}/v2/thread", headers=self._json_headers(), data=""
        )

    def get_thread(self, thread_id: str) -> LineAiResponse:
        """``GET /v2/thread/{id}`` — スレッド情報を取得する"""
        safe_id = requests.utils.quote(thread_id)
        return self.get(f"{self.host}/v2/thread/{safe_id}", headers=self._headers())

    def delete_thread(self, thread_id: str) -> LineAiResponse:
        """``DELETE /v2/thread/{id}`` — スレッドを削除する"""
        safe_id = requests.utils.quote(thread_id)
        return self.delete(
            f"{self.host}/v2/thread/{safe_id}", headers=self._headers()
        )

    def cancel_query(self, thread_id: str, run_id: str) -> LineAiResponse:
        """``POST /v2/query-ai/cancel`` — 実行中クエリをキャンセルする"""
        body = {"threadId": thread_id, "runId": run_id}
        return self.post(
            f"{self.host}/v2/query-ai/cancel",
            headers=self._json_headers(),
            json_data=body,
        )

    def query(
        self,
        thread_id: Optional[str] = None,
        message: str = "",
        image_url: Optional[str] = None,
    ) -> Generator[LineAiQueryChunk, None, None]:
        """``POST /v2/query-ai`` — AI クエリを実行し SSE ストリームを返す。

        Args:
            thread_id: スレッド ID。``None`` の場合は新規スレッドとして扱われる。
            message: ユーザーメッセージ。
            image_url: 添付画像 URL（省略可）。

        Yields:
            :class:`LineAiQueryChunk` — 各 SSE イベントのチャンク。

        Raises:
            :class:`StreamError`: SSE ストリームの解析に失敗した場合。
        """
        headers = self._headers(
            {
                "content-type": "application/json; charset=utf-8",
                "accept": "text/event-stream",
            }
        )
        payload = {
            "threadId": thread_id,
            "message": message,
            "imageUrl": image_url,
        }
        response = self._request(
            "POST",
            f"{self.host}/v2/query-ai",
            headers=headers,
            json_data=payload,
            stream=True,
        )
        try:
            for event in sseclient.SSEClient(response).events():
                chunk = LineAiQueryChunk.from_sse_block(event.data, event.event)
                if chunk:
                    yield chunk
        except Exception as exc:
            raise StreamError(f"SSE stream error: {exc}") from exc
