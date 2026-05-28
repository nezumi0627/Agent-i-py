"""基底APIクライアント"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

import requests

from .exceptions import ApiError, NetworkError
from .models import LineAiResponse, RateLimitInfo


class BaseApiClient:
    """HTTPリクエストを処理する基底クライアント。

    すべてのAPIクライアントはこのクラスを継承します。
    requests.Session を保持し、タイムアウト・エラーハンドリングを共通化します。
    """

    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout
        self.session = requests.Session()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _wrap_response(self, response: requests.Response) -> LineAiResponse:
        """レスポンスを LineAiResponse に変換し、HTTPエラーを例外に変換する"""
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise ApiError(
                f"HTTP {response.status_code} {response.reason}",
                status_code=response.status_code,
                body=response.text,
            ) from exc

        body: Any = None
        if response.text:
            try:
                body = json.loads(response.text)
            except json.JSONDecodeError:
                body = response.text

        return LineAiResponse(
            status=response.status_code,
            rate_limit=RateLimitInfo.from_headers(response.headers),
            body=body,
        )

    def _request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        json_data: Any = None,
        data: Any = None,
        stream: bool = False,
    ) -> requests.Response:
        """HTTPリクエストを実行する内部メソッド。

        stream=True の場合はエラーチェックを呼び出し側に委ねる。
        """
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
                data=data,
                stream=stream,
                timeout=self.timeout,
            )
            if not stream:
                self._raise_for_status(response)
            return response
        except requests.RequestException as exc:
            raise NetworkError(f"Network error: {exc}") from exc

    def _raise_for_status(self, response: requests.Response) -> None:
        """エラーレスポンスを ApiError に変換"""
        if not response.ok:
            raise ApiError(
                f"API error {response.status_code} {response.reason}",
                status_code=response.status_code,
                body=response.text,
            )

    # ------------------------------------------------------------------
    # Public HTTP methods
    # ------------------------------------------------------------------

    def get(
        self, url: str, *, headers: Optional[Dict[str, str]] = None
    ) -> LineAiResponse:
        """GETリクエスト"""
        return self._wrap_response(self._request("GET", url, headers=headers))

    def post(
        self,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        json_data: Any = None,
        data: Any = None,
    ) -> LineAiResponse:
        """POSTリクエスト"""
        return self._wrap_response(
            self._request("POST", url, headers=headers, json_data=json_data, data=data)
        )

    def delete(
        self, url: str, *, headers: Optional[Dict[str, str]] = None
    ) -> LineAiResponse:
        """DELETEリクエスト"""
        return self._wrap_response(self._request("DELETE", url, headers=headers))
