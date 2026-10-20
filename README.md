# Agent-i-py

LINEアプリとYahoo! Web版で観測した Agent I 関連APIを呼び出すPythonクライアントです。
HTTP通信、SSEストリーム、レスポンスモデル、例外をクライアントごとにまとめています。

## 対応API

| クライアント | 主な機能 | 認証 |
| --- | --- | --- |
| `AgentIClient` | Yahoo! WebViewの会話SSE、会話履歴 | 匿名Cookieを取得、または指定 |
| `LineAiClient` | LINE AIのスレッド・SSE、同意、可用性、AI操作、画像編集 | APIごとにチャネルトークンまたはLIFFアクセストークン |
| `YahooAgentClient` | Yahoo! Web版のタスクとアシスタント設定・メモリー | 認証Cookie、変更操作にはCSRF token、設定にはcrumb |

これらは非公式APIです。HARは限られたセッションの記録で、API仕様や提供継続を保証しません。詳しい観測範囲と制約は[HAR解析メモ](docs/har-analysis.md)を参照してください。

## インストール

Python 3.10以上が必要です。

```bash
python -m pip install .
```

開発ツールも含めてインストールする場合：

```bash
python -m pip install -e '.[dev]'
```

## 使い方

### Yahoo! WebViewの会話

匿名Cookieの取得は初回チャット時に行われます。各チャンクの`text`を順に読み取れます。

```python
from agent_i import AgentIClient

client = AgentIClient()
for chunk in client.chat("こんにちは"):
    if chunk.text:
        print(chunk.text, end="", flush=True)
```

### LINEアプリのネイティブAPI

トークンをソースへ直書きせず、環境変数などから渡してください。LINE AIの会話にはスレッドを作成して使います。

```python
import os

from agent_i import LineAiClient

client = LineAiClient(access_token=os.environ["LINE_AI_CHANNEL_TOKEN"])
thread = client.create_thread()
thread_id = thread.body["result"]["threadId"]

for chunk in client.query(thread_id=thread_id, message="こんにちは"):
    print(chunk.event, chunk.data)
```

チャット利用者情報・同意のAPIには`x-liff-access-token`用のトークンが別途必要です。画像編集は`get_image_edit_presets()`で取得したプリセットIDと履歴IDを`edit_image()`へ渡します。

### Yahoo! Web版のタスクと設定

認証Cookie、CSRF token、crumbは、利用者自身の認証済みセッションから安全に取得して渡します。

```python
import os

from agent_i import YahooAgentClient

client = YahooAgentClient(
    cookies=os.environ["YAHOO_COOKIES"],
    csrf_token=os.environ.get("YAHOO_CSRF_TOKEN", ""),
    crumb=os.environ.get("YAHOO_CRUMB", ""),
)

tasks = client.list_tasks(task_count=20)
memories = client.get_memories(size=5)
```

`YahooAgentClient`は一覧・概要の取得、タスク作成・更新・削除、メモリー取得、設定更新を提供します。作成・更新・削除には有効なCSRF tokenが必要です。

## レスポンスと例外

通常のHTTP APIは`LineAiResponse`を返し、`status`、`body`、`rate_limit`から結果を参照できます。SSE APIはチャンクを順にyieldします。API・通信・ストリームのエラーは`LineAiError`派生例外として通知します。

## テストと静的チェック

```bash
python -m pytest
python -m ruff check .
python -m mypy agent_i
```

認証情報が必要な統合テストは、対応する環境変数がない場合スキップされます。

## ライセンス

MIT License。詳細は[LICENSE](LICENSE)を参照してください。
