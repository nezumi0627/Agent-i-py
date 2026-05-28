"""LINE AI (Agent I) Python クライアント

このパッケージは LINE の Agent I（WebView および Native）の API をラップします。
"""
from __future__ import annotations

from .webview import AgentIClient
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

__all__ = [
    "AgentIClient",
    "LineAiClient",
    "AgentIConfig",
    "AgentSource",
    "ContextType",
    "LineAiConfig",
    "ApiError",
    "AuthenticationError",
    "LineAiError",
    "NetworkError",
    "RateLimitError",
    "StreamError",
    "AgentIChunk",
    "ChatMessage",
    "LineAiQueryChunk",
    "LineAiResponse",
    "RateLimitInfo",
    "ThreadInfo",
]
