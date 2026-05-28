"""基底APIクライアント"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

import requests

from .exceptions import ApiError, NetworkError
from .models import LineAiResponse, RateLimitInfo


class BaseApiClient:
    """HTTPリクエストを処理する基底クライアント"""

    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout
        self.session = requests.Session()

    def _wrap_response(self, response: requests.Response) -> LineAiResponse:
        """レスポンスをモデルに変換し、エラーをチェックする"""
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise ApiError(
                f"HTTP Error: {response.status_code} {response.reason}",
                status_code=response.status_code,
                body=response.text
            ) from e

        text = response.text
        body: Any = None
        if text:
            try:
                body = json.loads(text)
            except json.JSONDecodeError:
                body = text

        return LineAiResponse(
            status=response.status_code,
            rate_limit=RateLimitInfo.from_headers(response.headers),
            body=body
        )

    def _request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Any = None,
        data: Any = None,
        stream: bool = False,
    ) -> requests.Response:
        """HTTPリクエストを実行する内部メソッド"""
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
                data=data,
                stream=stream,
                timeout=self.timeout
            )
            if not stream:
                # stream=Trueの場合は呼び出し側でエラーチェックを行う
                self._check_error(response)
            return response
        except requests.RequestException as e:
            raise NetworkError(f"Network error occurred: {str(e)}") from e

    def _check_error(self, response: requests.Response) -> None:
        """エラーがあれば例外を送出"""
        if not response.ok:
            raise ApiError(
                f"API Error: {response.status_code} {response.reason}",
                status_code=response.status_code,
                body=response.text
            )

    def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> LineAiResponse:
        """GETリクエスト"""
        response = self._request("GET", url, headers=headers)
        return self._wrap_response(response)

    def post(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Any = None,
        data: Any = None,
    ) -> LineAiResponse:
        """POSTリクエスト"""
        response = self._request("POST", url, headers=headers, json_data=json_data, data=data)
        return self._wrap_response(response)

    def delete(self, url: str, headers: Optional[Dict[str, str]] = None) -> LineAiResponse:
        """DELETEリクエスト"""
        response = self._request("DELETE", url, headers=headers)
        return self._wrap_response(response)
