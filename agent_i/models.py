"""LINE AI クライアントのデータモデル"""

from __future__ import annotations

import contextlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass
class ThreadInfo:
    """スレッド情報"""

    thread_id: str
    encryption_key: str

    # 後方互換エイリアス（snake_case に統一、旧 camelCase も維持）
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ThreadInfo:
        """APIレスポンス辞書からインスタンスを生成"""
        return cls(
            thread_id=data.get("threadId", ""),
            encryption_key=data.get("encryptionKey", ""),
        )


@dataclass
class ChatMessage:
    """チャットメッセージ"""

    id: str
    role: str
    contents: list[dict[str, str]]

    def to_dict(self) -> dict[str, Any]:
        """辞書表現に変換"""
        return {"id": self.id, "role": self.role, "contents": self.contents}


@dataclass
class AgentIChunk:
    """Agent I (WebView) 用 SSE チャンク"""

    event: str | None
    data: Any
    text: str | None

    @classmethod
    def from_sse_event(cls, data: str, event_name: str | None = None) -> AgentIChunk | None:
        """SSEイベントデータからインスタンスを生成"""
        if not data:
            return None

        parsed: Any = data
        if data.startswith(("{", "[")):
            with contextlib.suppress(json.JSONDecodeError):
                parsed = json.loads(data)

        return cls(event=event_name, data=parsed, text=cls._extract_text(parsed))

    @staticmethod
    def _extract_text(data: Any) -> str | None:
        """ペイロードからテキストを抽出"""
        if isinstance(data, str):
            return data

        if not data or not isinstance(data, dict):
            return None

        # Yahoo search-agent wire shape
        if data.get("type") in ("compositeMessage-delta", "compositeMessage-end"):
            value = data.get("value")
            if isinstance(value, dict):
                msg = value.get("message")
                if isinstance(msg, str):
                    return msg
                if isinstance(msg, dict) and isinstance(msg.get("text"), str):
                    return str(msg["text"])

        # 一般的なフォールバック
        for key in ("text", "delta", "content"):
            val = data.get(key)
            if isinstance(val, str):
                return val

        # contents 配列
        contents = data.get("contents")
        if isinstance(contents, list):
            parts = [
                c["text"]
                for c in contents
                if isinstance(c, dict) and isinstance(c.get("text"), str)
            ]
            if parts:
                return "".join(parts)

        return None


@dataclass
class LineAiQueryChunk:
    """ネイティブ LINE AI 用 SSE チャンク"""

    event: str | None
    data: Any

    @classmethod
    def from_sse_block(cls, block: str, event_name: str | None = None) -> LineAiQueryChunk:
        """SSEブロックテキストからインスタンスを生成"""
        event = event_name
        data_lines: list[str] = []

        for line in block.split("\n"):
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].strip())

        raw = "\n".join(data_lines)
        parsed: Any = raw
        if raw:
            with contextlib.suppress(json.JSONDecodeError):
                parsed = json.loads(raw)

        return cls(event=event, data=parsed)


@dataclass
class RateLimitInfo:
    """レートリミット情報"""

    limit: str | None = None
    remaining: str | None = None
    usage: str | None = None

    @classmethod
    def from_headers(cls, headers: Any) -> RateLimitInfo:
        """レスポンスヘッダーからレートリミット情報を抽出"""
        return cls(
            limit=headers.get("x-ratelimit-limit"),
            remaining=headers.get("x-ratelimit-remaining"),
            usage=headers.get("x-ratelimit-usage"),
        )


@dataclass
class LineAiResponse:
    """API レスポンスラッパー"""

    status: int
    rate_limit: RateLimitInfo
    body: Any

    @property
    def is_success(self) -> bool:
        """リクエストが成功したかどうか"""
        return 200 <= self.status < 300
