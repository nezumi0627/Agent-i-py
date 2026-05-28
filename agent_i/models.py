"""LINE AI クライアントのデータモデル"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ThreadInfo:
    """スレッド情報"""

    threadId: str
    encryptionKey: str


@dataclass
class ChatMessage:
    """チャットメッセージ"""

    id: str
    role: str
    contents: List[Dict[str, str]]


@dataclass
class AgentIChunk:
    """Agent I (WebView) 用 SSE チャンク"""

    event: Optional[str]
    data: Any
    text: Optional[str]

    @classmethod
    def from_sse_event(cls, data: str, event_name: Optional[str] = None) -> Optional["AgentIChunk"]:
        """SSEイベントデータからインスタンスを生成"""
        if not data:
            return None

        parsed_data = data
        if data.startswith("{") or data.startswith("["):
            try:
                parsed_data = json.loads(data)
            except json.JSONDecodeError:
                pass

        return cls(
            event=event_name,
            data=parsed_data,
            text=cls._extract_text(parsed_data)
        )

    @staticmethod
    def _extract_text(data: Any) -> Optional[str]:
        """ペイロードからテキストを抽出"""
        if isinstance(data, str):
            return data

        if not data or not isinstance(data, dict):
            return None

        # Yahoo search-agent wire shape
        if data.get("type") in ["compositeMessage-delta", "compositeMessage-end"]:
            value = data.get("value")
            if isinstance(value, dict) and isinstance(value.get("message"), str):
                return value["message"]
            if isinstance(value, dict) and isinstance(value.get("message"), dict):
                msg = value.get("message", {})
                if isinstance(msg.get("text"), str):
                     return msg["text"]

        # 一般的なフォールバック
        for key in ["text", "delta", "content"]:
            if isinstance(data.get(key), str):
                return data[key]

        # contents配列
        contents = data.get("contents")
        if isinstance(contents, list):
            parts = [c["text"] for c in contents if isinstance(c, dict) and isinstance(c.get("text"), str)]
            if parts:
                return "".join(parts)

        return None


@dataclass
class LineAiQueryChunk:
    """ネイティブ LINE AI 用 SSE チャンク"""

    event: Optional[str]
    data: Any

    @classmethod
    def from_sse_block(cls, block: str, event_name: Optional[str] = None) -> "LineAiQueryChunk":
        """SSEブロックテキストからインスタンスを生成"""
        lines = block.split('\n')
        event = event_name
        data_lines = []

        for line in lines:
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].strip())

        raw = "\n".join(data_lines)
        data: Any = raw
        if raw:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                pass

        return cls(event=event, data=data)


@dataclass
class RateLimitInfo:
    """レートリミット情報"""

    limit: Optional[str] = None
    remaining: Optional[str] = None
    usage: Optional[str] = None

    @classmethod
    def from_headers(cls, headers: Dict[str, str]) -> "RateLimitInfo":
        """レスポンスヘッダーからレートリミット情報を抽出"""
        # headers is usually case-insensitive dict in requests, but mapping for safety
        return cls(
            limit=headers.get("x-ratelimit-limit"),
            remaining=headers.get("x-ratelimit-remaining"),
            usage=headers.get("x-ratelimit-usage")
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
