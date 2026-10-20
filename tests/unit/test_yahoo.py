"""Yahoo Agent API client behavior."""

from __future__ import annotations

from unittest.mock import Mock, patch

from agent_i import YahooAgentClient


def response() -> Mock:
    result = Mock()
    result.ok = True
    result.status_code = 200
    result.reason = "OK"
    result.text = "{}"
    result.headers = {}
    return result


class TestYahooAgentClient:
    @patch("agent_i.base.requests.Session.request")
    def test_lists_tasks_with_count(self, request: Mock) -> None:
        request.return_value = response()
        client = YahooAgentClient(cookies="session=cookie")

        client.list_tasks(task_count=20)

        call = request.call_args.kwargs
        assert call["method"] == "GET"
        assert call["url"].endswith("/v1/users/tasks?task_count=20")
        assert call["headers"]["cookie"] == "session=cookie"

    @patch("agent_i.base.requests.Session.request")
    def test_gets_task_overview(self, request: Mock) -> None:
        request.return_value = response()
        client = YahooAgentClient()

        client.get_task_overview()

        call = request.call_args.kwargs
        assert call["method"] == "GET"
        assert call["url"].endswith("/v1/users/tasks/agent-top")

    @patch("agent_i.base.requests.Session.request")
    def test_creates_task_with_csrf_header_and_payload(self, request: Mock) -> None:
        request.return_value = response()
        client = YahooAgentClient(csrf_token="csrf-value")
        payload = {"title": "daily task"}

        client.create_task(payload)

        call = request.call_args.kwargs
        assert call["method"] == "POST"
        assert call["headers"]["x-csrf-token"] == "csrf-value"
        assert call["json"] == payload

    @patch("agent_i.base.requests.Session.request")
    def test_encodes_task_id_and_updates_with_patch(self, request: Mock) -> None:
        request.return_value = response()
        client = YahooAgentClient(csrf_token="csrf-value")

        client.update_task("task/id", {"is_notify": True})

        call = request.call_args.kwargs
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/v1/users/tasks/task%2Fid")
        assert call["json"] == {"is_notify": True}

    @patch("agent_i.base.requests.Session.request")
    def test_requests_memories_with_pagination_and_crumb(self, request: Mock) -> None:
        request.return_value = response()
        client = YahooAgentClient(crumb="crumb-value")

        client.get_memories(size=10, sort_by="updatedAt", order="desc")

        call = request.call_args.kwargs
        assert call["url"].endswith("?size=10&sortBy=updatedAt&order=desc")
        assert call["headers"]["x-auth-token-type"] == "crumb"
        assert call["headers"]["x-crumb"] == "crumb-value"

    @patch("agent_i.base.requests.Session.request")
    def test_updates_settings_with_personalization_headers(self, request: Mock) -> None:
        request.return_value = response()
        client = YahooAgentClient(crumb="crumb-value")
        settings = {"assistant": {"useMemory": False}}

        client.update_settings(settings)

        call = request.call_args.kwargs
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/api/v1/settings")
        assert call["headers"]["x-crumb"] == "crumb-value"
        assert call["json"] == {"settings": settings}

    @patch("agent_i.base.requests.Session.request")
    def test_deletes_task_with_encoded_id(self, request: Mock) -> None:
        request.return_value = response()
        client = YahooAgentClient()

        client.delete_task("task/one")

        call = request.call_args.kwargs
        assert call["method"] == "DELETE"
        assert call["url"].endswith("/v1/users/tasks/task%2Fone")
