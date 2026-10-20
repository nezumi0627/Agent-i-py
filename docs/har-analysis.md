# Agent I communication observed in HAR captures

The captures were inspected on 2026-10-20. This inventory records hosts, paths,
methods and payload shape only. It intentionally excludes cookie/token values,
personal data, and message text.

## LINE app capture

| Host | Method and path | Purpose / observed result |
| --- | --- | --- |
| `chat-ai.line-apps.com` | `GET /ai-ts/v1/availability` | AI terms and feature availability |
| `chat-ai.line-apps.com` | `POST /ai-ts/v1/operation` | AI operations: message suggestion, talk mood, search-query recommendation, TMI bot; some responses were 403/429 |
| `ai-chat-public.line-apps.com` | `GET /v1/user/info` | Subscription and user feature status |
| `ai-chat-public.line-apps.com` | `POST /v1/user-agreement` | Communication-information agreement; 204 observed |
| `line-x-openai.line-apps.com` | `GET /v2/image-edit/prompt-preset` | Image editing preset list and history ID |
| `line-x-openai.line-apps.com` | `POST /v2/image-edit` | Image URL, preset ID, and history ID; returns run ID and output URLs |
| `line-x-openai.line-apps.com` | `/v2/service-info`, `/v2/user/agreement`, `/v2/thread`, `/v2/query-ai` | Existing library methods; not present in this capture's observed requests |
| `agent-task.yahoo.co.jp` | `GET /v1/users/tasks/agent-top` | LINE embedded task overview; empty task list observed |
| `uts-front.line-apps.com` | `POST /event`, `/event-web`, `GET /settings` | Frontend telemetry/settings, not Agent I business APIs |

## Yahoo web capture

| Host | Method and path | Purpose / observed result |
| --- | --- | --- |
| `agent-task.yahoo.co.jp` | `GET /v1/users/tasks` | List tasks; `task_count` query parameter observed |
| `agent-task.yahoo.co.jp` | `GET /v1/users/tasks/agent-top` | Overview and registration counts |
| `agent-task.yahoo.co.jp` | `POST /v1/users/tasks` | Create scheduled/repeating task with form components and task settings |
| `agent-task.yahoo.co.jp` | `PATCH /v1/users/tasks/{task_id}` | Update schedule, notification, repeat, and opt-in settings |
| `agent-task.yahoo.co.jp` | `DELETE /v1/users/tasks/{task_id}` | Delete task |
| `agent-personalize.yahoo.co.jp` | `GET /api/v1/memories` | Paginated memory list (`size`, `sortBy`, `order`) |
| `agent-personalize.yahoo.co.jp` | `PATCH /api/v1/settings` | Assistant nickname, tone, and memory preference |

## Limits

HAR captures represent the captured sessions, not a complete or stable API
specification. Several operations returned authorization or rate-limit errors;
the request schema is observable but successful behavior is not verified. The
Yahoo task client requires an authenticated cookie and, for mutations, the
session's CSRF token. Personalization uses the session crumb. LINE's operation
API payloads vary by operation, so `operate_ai` accepts an operation name and
its matching parameter object without claiming an exhaustive schema.
