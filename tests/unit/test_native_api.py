"""LINE app API endpoints observed in the app capture."""

from __future__ import annotations

from unittest.mock import Mock, patch

from agent_i import LineAiClient


def response() -> Mock:
    result = Mock()
    result.ok = True
    result.status_code = 200
    result.reason = "OK"
    result.text = "{}"
    result.headers = {}
    return result


class TestNativeObservedEndpoints:
    @patch("agent_i.base.requests.Session.request")
    def test_get_user_info_uses_liff_token(self, request: Mock) -> None:
        request.return_value = response()

        LineAiClient(access_token="channel-token").get_user_info("liff-token")

        call = request.call_args.kwargs
        assert call["url"].endswith("/v1/user/info")
        assert call["headers"]["x-liff-access-token"] == "liff-token"

    @patch("agent_i.base.requests.Session.request")
    def test_submit_chat_agreement_sends_agreement_fields(self, request: Mock) -> None:
        request.return_value = response()

        LineAiClient(access_token="channel-token").submit_chat_agreement(
            "liff-token", communication_info=False, version="v2"
        )

        call = request.call_args.kwargs
        assert call["method"] == "POST"
        assert call["json"] == {"communicationInfo": False, "communicationInfoVersion": "v2"}

    @patch("agent_i.base.requests.Session.request")
    def test_checks_ai_availability(self, request: Mock) -> None:
        request.return_value = response()

        LineAiClient(access_token="channel-token").check_ai_availability(lang_code="ja-JP")

        assert request.call_args.kwargs["url"].endswith("/ai-ts/v1/availability?lang_code=ja-JP")

    @patch("agent_i.base.requests.Session.request")
    def test_encodes_availability_language_as_query_value(self, request: Mock) -> None:
        request.return_value = response()

        LineAiClient(access_token="channel-token").check_ai_availability(lang_code="ja&x=y")

        assert request.call_args.kwargs["url"].endswith(
            "/ai-ts/v1/availability?lang_code=ja%26x%3Dy"
        )

    @patch("agent_i.base.requests.Session.request")
    def test_operates_ai_with_operation_and_params(self, request: Mock) -> None:
        request.return_value = response()

        LineAiClient(access_token="channel-token").operate_ai("operation", {"query": "hello"})

        assert request.call_args.kwargs["json"] == {
            "op": "operation",
            "params": {"query": "hello"},
        }

    @patch("agent_i.base.requests.Session.request")
    def test_edits_image_using_observed_wire_shape(self, request: Mock) -> None:
        request.return_value = response()

        LineAiClient(access_token="channel-token").edit_image(
            ["https://example.test/image.jpg"], "preset", 123
        )

        call = request.call_args.kwargs
        assert call["url"].endswith("/v2/image-edit")
        assert call["json"] == {
            "imageList": [{"url": "https://example.test/image.jpg"}],
            "presetId": "preset",
            "historyId": 123,
        }
