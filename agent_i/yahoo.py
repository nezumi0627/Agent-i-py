"""Yahoo! Agent task and personalization APIs observed in the web client."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote, urlencode

from .base import BaseApiClient
from .config import AgentIConfig
from .models import LineAiResponse


class YahooAgentClient(BaseApiClient):
    """Client for Yahoo Agent tasks and assistant personalization.

    Supply browser cookies and the CSRF/crumb headers from an authorized session.
    Credentials are never extracted from or stored in HAR files by this client.
    """

    def __init__(
        self,
        *,
        cookies: str = "",
        csrf_token: str = "",
        crumb: str = "",
        timeout: int = 30,
    ) -> None:
        super().__init__(timeout=timeout)
        self.cookies = cookies
        self.csrf_token = csrf_token
        self.crumb = crumb

    def _headers(self, *, csrf: bool = False, personalize: bool = False) -> dict[str, str]:
        headers = {"accept": "application/json"}
        if self.cookies:
            headers["cookie"] = self.cookies
        if csrf and self.csrf_token:
            headers["x-csrf-token"] = self.csrf_token
        if personalize:
            headers["x-auth-token-type"] = "crumb"
            if self.crumb:
                headers["x-crumb"] = self.crumb
        return headers

    def list_tasks(self, *, task_count: int | None = None) -> LineAiResponse:
        """List tasks (``GET /v1/users/tasks``)."""
        query = f"?{urlencode({'task_count': task_count})}" if task_count is not None else ""
        return self.get(f"{AgentIConfig.TASK_HOST}/v1/users/tasks{query}", headers=self._headers())

    def get_task_overview(self) -> LineAiResponse:
        """Get task overview and counts (``GET /v1/users/tasks/agent-top``)."""
        return self.get(
            f"{AgentIConfig.TASK_HOST}/v1/users/tasks/agent-top", headers=self._headers()
        )

    def create_task(self, task: dict[str, Any]) -> LineAiResponse:
        """Create a task (``POST /v1/users/tasks``)."""
        return self.post(
            f"{AgentIConfig.TASK_HOST}/v1/users/tasks",
            headers=self._headers(csrf=True),
            json_data=task,
        )

    def update_task(self, task_id: str, changes: dict[str, Any]) -> LineAiResponse:
        """Update a task (``PATCH /v1/users/tasks/{task_id}``)."""
        return self.patch(
            f"{AgentIConfig.TASK_HOST}/v1/users/tasks/{quote(task_id, safe='')}",
            headers=self._headers(csrf=True),
            json_data=changes,
        )

    def delete_task(self, task_id: str) -> LineAiResponse:
        """Delete a task (``DELETE /v1/users/tasks/{task_id}``)."""
        return self.delete(
            f"{AgentIConfig.TASK_HOST}/v1/users/tasks/{quote(task_id, safe='')}",
            headers=self._headers(csrf=True),
        )

    def get_memories(
        self, *, size: int = 5, sort_by: str | None = None, order: str | None = None
    ) -> LineAiResponse:
        """Get assistant memories (``GET /api/v1/memories``)."""
        params: dict[str, Any] = {"size": size}
        if sort_by:
            params["sortBy"] = sort_by
        if order:
            params["order"] = order
        return self.get(
            f"{AgentIConfig.PERSONALIZE_HOST}/api/v1/memories?{urlencode(params)}",
            headers=self._headers(personalize=True),
        )

    def update_settings(self, settings: dict[str, Any]) -> LineAiResponse:
        """Update assistant settings (``PATCH /api/v1/settings``)."""
        return self.patch(
            f"{AgentIConfig.PERSONALIZE_HOST}/api/v1/settings",
            headers={**self._headers(personalize=True), "content-type": "application/json"},
            json_data={"settings": settings},
        )
