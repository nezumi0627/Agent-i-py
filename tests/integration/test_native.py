"""
LineAiClient 統合テスト

実際のネットワークアクセスが必要なため、通常の CI では skip します。
LINE_AI_CHANNEL_TOKEN 環境変数が設定されている場合のみ実行されます。

実行方法:
    LINE_AI_CHANNEL_TOKEN=xxx pytest tests/integration/ -v
"""
from __future__ import annotations

import os

import pytest

from agent_i import LineAiClient
from agent_i.exceptions import LineAiError

TOKEN = os.getenv("LINE_AI_CHANNEL_TOKEN", "")
skip_if_no_token = pytest.mark.skipif(
    not TOKEN, reason="LINE_AI_CHANNEL_TOKEN not set"
)


@skip_if_no_token
class TestLineAiClientIntegration:
    """実環境に対する結合テスト（要チャネルトークン）"""

    @pytest.fixture
    def client(self) -> LineAiClient:
        return LineAiClient(access_token=TOKEN)

    def test_get_service_info(self, client: LineAiClient) -> None:
        res = client.get_service_info()
        assert res.is_success

    def test_full_query_flow(self, client: LineAiClient) -> None:
        client.submit_agreement()
        thread_res = client.create_thread()
        assert thread_res.is_success

        thread_id = thread_res.body["result"]["threadId"]
        chunks = list(client.query(thread_id=thread_id, message="Hello"))
        assert len(chunks) > 0

        client.delete_thread(thread_id)
