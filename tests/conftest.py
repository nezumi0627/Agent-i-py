"""pytest 共通フィクスチャ"""
from __future__ import annotations

import pytest

from agent_i import AgentIClient, LineAiClient


@pytest.fixture
def webview_client() -> AgentIClient:
    """クッキー設定済みの AgentIClient"""
    return AgentIClient(cookies="B=dummy; XB=dummy")


@pytest.fixture
def native_client() -> LineAiClient:
    """テスト用 LineAiClient"""
    return LineAiClient(access_token="test_token")
