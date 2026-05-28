"""ネイティブ LINE AI クライアント"""
from __future__ import annotations

from typing import Dict, Generator, Optional
import requests
import sseclient

from .base import BaseApiClient
from .config import LineAiConfig, ContextType
from .exceptions import StreamError
from .models import LineAiQueryChunk, LineAiResponse


class LineAiClient(BaseApiClient):
    """ネイティブLINE AIクライアント
    
    com.linecorp.line.lineai.impl.ui.LineAiActivity で使用される
    ネイティブLINE AI APIのラッパー
    """

    def __init__(
        self,
        access_token: str,
        line_version: str = LineAiConfig.DEFAULT_LINE_VERSION,
        line_os: str = LineAiConfig.DEFAULT_LINE_OS,
        host: str = LineAiConfig.DEFAULT_HOST,
        accept_language: str = LineAiConfig.DEFAULT_ACCEPT_LANGUAGE,
        timeout: int = 30
    ) -> None:
        """
        Args:
            access_token: LINE AIチャネルトークン（生のLINEアクセストークンではない）
            line_version: LINEアプリのバージョン
            line_os: LINEアプリのOS
            host: APIホスト（省略時はデフォルトホスト）
            accept_language: Accept-Languageヘッダー
            timeout: リクエストタイムアウト
        """
        super().__init__(timeout=timeout)
        self.access_token = access_token
        self.line_version = line_version
        self.line_os = line_os
        self.host = host.rstrip("/")
        self.accept_language = accept_language

    def _build_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """リクエストヘッダーを構築"""
        headers = {
            "accept": "application/json",
            "user-agent": f"LINE/{self.line_version} CFNetwork/3860.200.71 Darwin/25.1.0",
            "x-access-token": self.access_token,
            "x-line-version": self.line_version,
            "x-line-os": self.line_os,
            "accept-language": self.accept_language,
        }
        if extra:
            headers.update(extra)
        return headers

    def get_service_info(self) -> LineAiResponse:
        """GET /v2/service-info — AIサービスリストを取得"""
        return self.get(f"{self.host}/v2/service-info", headers=self._build_headers())

    def get_prompt_presets(
        self,
        context_type: ContextType | str,
        accept_language: Optional[str] = None
    ) -> LineAiResponse:
        """GET /v2/{contextType}/prompt-preset — コンテキスト別のプロンプトプリセットを取得"""
        ctx = ContextType(context_type).value if isinstance(context_type, str) else context_type.value
        
        extra_headers = {}
        if accept_language:
            extra_headers["accept-language"] = accept_language
            
        return self.get(
            f"{self.host}/v2/{ctx}/prompt-preset",
            headers=self._build_headers(extra_headers)
        )

    def submit_agreement(self) -> LineAiResponse:
        """POST /v2/user/agreement — 利用規約に同意"""
        headers = self._build_headers({"content-type": "application/json; charset=utf-8"})
        return self.post(f"{self.host}/v2/user/agreement", headers=headers, data="")

    def create_thread(self) -> LineAiResponse:
        """POST /v2/thread — 新しいスレッドを作成"""
        headers = self._build_headers({"content-type": "application/json; charset=utf-8"})
        return self.post(f"{self.host}/v2/thread", headers=headers, data="")

    def get_thread(self, thread_id: str) -> LineAiResponse:
        """GET /v2/thread/{id} — スレッド情報を取得"""
        safe_id = requests.utils.quote(thread_id)
        return self.get(f"{self.host}/v2/thread/{safe_id}", headers=self._build_headers())

    def delete_thread(self, thread_id: str) -> LineAiResponse:
        """DELETE /v2/thread/{id} — スレッドを削除"""
        safe_id = requests.utils.quote(thread_id)
        return self.delete(f"{self.host}/v2/thread/{safe_id}", headers=self._build_headers())

    def cancel_query(self, thread_id: str, run_id: str) -> LineAiResponse:
        """POST /v2/query-ai/cancel — クエリをキャンセル"""
        headers = self._build_headers({"content-type": "application/json; charset=utf-8"})
        body = {"threadId": thread_id, "runId": run_id}
        return self.post(f"{self.host}/v2/query-ai/cancel", headers=headers, json_data=body)

    def query(
        self,
        thread_id: Optional[str] = None,
        message: str = "",
        image_url: Optional[str] = None
    ) -> Generator[LineAiQueryChunk, None, None]:
        """POST /v2/query-ai — AIクエリを実行し、SSEストリームから応答を取得"""
        headers = self._build_headers({
            "content-type": "application/json; charset=utf-8",
            "accept": "text/event-stream"
        })

        payload = {
            "threadId": thread_id,
            "message": message,
            "imageUrl": image_url
        }

        response = self._request(
            "POST",
            f"{self.host}/v2/query-ai",
            headers=headers,
            json_data=payload,
            stream=True
        )

        try:
            client = sseclient.SSEClient(response)
            for event in client.events():
                chunk = LineAiQueryChunk.from_sse_block(event.data, event.event)
                if chunk:
                    yield chunk
        except Exception as e:
            raise StreamError(f"Error parsing query-ai SSE stream: {str(e)}") from e
