"""LINE AI クライアント設定定数・列挙型"""

from __future__ import annotations

from enum import Enum


class AgentSource(str, Enum):
    """Agent I 呼び出し元ソース種別"""

    CHAT_TAB = "chattab_searchbar"
    HOME_TAB = "hometab_searchbar"
    NEWS_TAB = "newstab_searchbar"

    @property
    def frcode(self) -> str:
        """frcode パラメータ値"""
        return f"line_agenti_{self.value}"

    @property
    def frtype(self) -> str:
        """frtype パラメータ値"""
        return f"line_{self.value}"


class ContextType(str, Enum):
    """プロンプトプリセットのコンテキスト種別"""

    TRENDING = "trending"
    IMAGE_ATTACHED = "image-attached"


class LineAiConfig:
    """LineAiClient 設定定数"""

    CHANNEL_ID: str = "2006890580"
    DEFAULT_HOST: str = "https://line-x-openai.line-apps.com"
    ALPHA_HOST: str = "https://line-x-openai.line-apps-alpha.com"
    DEFAULT_LINE_VERSION: str = "26.7.2"
    DEFAULT_LINE_OS: str = "IOS"
    DEFAULT_ACCEPT_LANGUAGE: str = "ja"
    CHAT_HOST: str = "https://chat-ai.line-apps.com"
    PUBLIC_HOST: str = "https://ai-chat-public.line-apps.com"


class AgentIConfig:
    """AgentIClient 設定定数"""

    DEFAULT_ENDPOINT: str = "https://agt.search.yahoo.co.jp/v2/chat"
    WEBVIEW_BASE_URL: str = "https://search.yahoo.co.jp/chat"
    DEFAULT_LINE_VERSION: str = "26.7.2"
    DEFAULT_SOURCE: AgentSource = AgentSource.CHAT_TAB
    TASK_HOST: str = "https://agent-task.yahoo.co.jp"
    PERSONALIZE_HOST: str = "https://agent-personalize.yahoo.co.jp"
