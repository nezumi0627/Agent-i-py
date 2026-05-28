"""LINE AI (Agent I) Python クライアント

このパッケージは LINE の Agent I（WebView および Native）の API をラップします。

クイックスタート::

    # WebView パス（認証不要）
    from agent_i import AgentIClient

    client = AgentIClient()
    for chunk in client.chat("こんにちは"):
        if chunk.text:
            print(chunk.text, end="", flush=True)

    # Native パス（チャネルトークン必要）
    from agent_i import LineAiClient

    client = LineAiClient(access_token="YOUR_TOKEN")
    client.submit_agreement()
    res = client.create_thread()
    thread_id = res.body["result"]["threadId"]
    for chunk in client.query(thread_id=thread_id, message="元気？"):
        print(chunk.data)
"""
from __future__ import annotations

from .config import AgentIConfig, AgentSource, ContextType, LineAiConfig
from .exceptions import (
    ApiError,
    AuthenticationError,
    LineAiError,
    NetworkError,
    RateLimitError,
    StreamError,
)
from .models import (
    AgentIChunk,
    ChatMessage,
    LineAiQueryChunk,
    LineAiResponse,
    RateLimitInfo,
    ThreadInfo,
)
from .native import LineAiClient
from .webview import AgentIClient

__all__ = [
    # Clients
    "AgentIClient",
    "LineAiClient",
    # Config
    "AgentIConfig",
    "AgentSource",
    "ContextType",
    "LineAiConfig",
    # Exceptions
    "ApiError",
    "AuthenticationError",
    "LineAiError",
    "NetworkError",
    "RateLimitError",
    "StreamError",
    # Models
    "AgentIChunk",
    "ChatMessage",
    "LineAiQueryChunk",
    "LineAiResponse",
    "RateLimitInfo",
    "ThreadInfo",
]

__version__ = "1.1.0"
