"""LINE AI クライアント例外階層"""
from __future__ import annotations


class LineAiError(Exception):
    """LINE AI クライアントの基底例外クラス"""


class AuthenticationError(LineAiError):
    """認証エラー（無効・期限切れトークンなど）"""


class RateLimitError(LineAiError):
    """レートリミット超過エラー"""

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class ApiError(LineAiError):
    """APIエラー（4xx / 5xx レスポンス）"""

    def __init__(self, message: str, *, status_code: int, body: str = "") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class NetworkError(LineAiError):
    """ネットワーク接続エラー"""


class StreamError(LineAiError):
    """SSEストリーム解析エラー"""
