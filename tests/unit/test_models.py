"""モデルクラスの単体テスト"""
from __future__ import annotations

import pytest

from agent_i.models import (
    AgentIChunk,
    ChatMessage,
    LineAiQueryChunk,
    LineAiResponse,
    RateLimitInfo,
    ThreadInfo,
)


class TestThreadInfo:
    def test_from_dict(self):
        info = ThreadInfo.from_dict({"threadId": "t1", "encryptionKey": "k1"})
        assert info.thread_id == "t1"
        assert info.encryption_key == "k1"

    def test_from_dict_missing_keys(self):
        info = ThreadInfo.from_dict({})
        assert info.thread_id == ""
        assert info.encryption_key == ""


class TestChatMessage:
    def test_to_dict(self):
        msg = ChatMessage(id="id1", role="user", contents=[{"type": "text", "text": "hi"}])
        d = msg.to_dict()
        assert d["id"] == "id1"
        assert d["role"] == "user"
        assert d["contents"] == [{"type": "text", "text": "hi"}]


class TestAgentIChunk:
    """AgentIChunk._extract_text の各ケース"""

    def test_plain_string(self):
        assert AgentIChunk._extract_text("hello") == "hello"

    def test_composite_message_delta_str(self):
        data = {"type": "compositeMessage-delta", "value": {"message": "test"}}
        assert AgentIChunk._extract_text(data) == "test"

    def test_composite_message_delta_dict_message(self):
        data = {"type": "compositeMessage-delta", "value": {"message": {"text": "test2"}}}
        assert AgentIChunk._extract_text(data) == "test2"

    def test_composite_message_end(self):
        data = {"type": "compositeMessage-end", "value": {"message": "done"}}
        assert AgentIChunk._extract_text(data) == "done"

    def test_text_field_fallback(self):
        assert AgentIChunk._extract_text({"text": "hi"}) == "hi"

    def test_delta_field_fallback(self):
        assert AgentIChunk._extract_text({"delta": "delta"}) == "delta"

    def test_content_field_fallback(self):
        assert AgentIChunk._extract_text({"content": "c"}) == "c"

    def test_contents_array(self):
        data = {"contents": [{"text": "hello"}, {"text": "world"}]}
        assert AgentIChunk._extract_text(data) == "helloworld"

    def test_none_data(self):
        assert AgentIChunk._extract_text(None) is None

    def test_empty_dict(self):
        assert AgentIChunk._extract_text({}) is None

    def test_from_sse_event_empty(self):
        assert AgentIChunk.from_sse_event("") is None

    def test_from_sse_event_json(self):
        chunk = AgentIChunk.from_sse_event(
            '{"type": "compositeMessage-delta", "value": {"message": "hello"}}',
            "compositeMessage-delta",
        )
        assert chunk is not None
        assert chunk.text == "hello"
        assert chunk.event == "compositeMessage-delta"

    def test_from_sse_event_plain_text(self):
        chunk = AgentIChunk.from_sse_event("plain text")
        assert chunk is not None
        assert chunk.text == "plain text"


class TestLineAiQueryChunk:
    def test_from_sse_block_json(self):
        block = 'event: run.started\ndata: {"runId": "R1"}'
        chunk = LineAiQueryChunk.from_sse_block(block)
        assert chunk.event == "run.started"
        assert chunk.data == {"runId": "R1"}

    def test_from_sse_block_plain(self):
        block = "data: plain text"
        chunk = LineAiQueryChunk.from_sse_block(block)
        assert chunk.data == "plain text"

    def test_from_sse_block_event_name_override(self):
        block = "data: x"
        chunk = LineAiQueryChunk.from_sse_block(block, event_name="custom")
        assert chunk.event == "custom"


class TestRateLimitInfo:
    def test_from_headers(self):
        headers = {
            "x-ratelimit-limit": "100",
            "x-ratelimit-remaining": "90",
            "x-ratelimit-usage": "10",
        }
        rl = RateLimitInfo.from_headers(headers)
        assert rl.limit == "100"
        assert rl.remaining == "90"
        assert rl.usage == "10"

    def test_from_headers_missing(self):
        rl = RateLimitInfo.from_headers({})
        assert rl.limit is None


class TestLineAiResponse:
    def test_is_success_200(self):
        res = LineAiResponse(status=200, rate_limit=RateLimitInfo(), body={})
        assert res.is_success is True

    def test_is_success_299(self):
        res = LineAiResponse(status=299, rate_limit=RateLimitInfo(), body={})
        assert res.is_success is True

    def test_is_not_success_400(self):
        res = LineAiResponse(status=400, rate_limit=RateLimitInfo(), body={})
        assert res.is_success is False

    def test_is_not_success_500(self):
        res = LineAiResponse(status=500, rate_limit=RateLimitInfo(), body={})
        assert res.is_success is False
