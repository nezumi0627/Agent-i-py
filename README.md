# Agent-i-py

LINE AI（Agent I）の強力でPythonicなクライアントライブラリです。WebView版とNative版の両方のAPIに対応し、完全にオブジェクト指向で型安全な設計になっています。

## 特徴

- **WebView パス (`AgentIClient`)**: Yahooの匿名クッキーを自動取得し、Yahooログイン不要で会話履歴管理を行います。
- **Native パス (`LineAiClient`)**: LINEアプリのネイティブAPIをラッピング。チャネルトークンを使用してスレッド管理などを実行します。
- **完全な型ヒント**: Data class と Enum を多用し、IDEの強力な補完に対応しています。
- **エラーハンドリング**: 詳細な例外クラス (`LineAiError`, `ApiError`, `NetworkError` など) を提供しています。

## インストール

```bash
pip install .
```

または要件ファイルをインストール：

```bash
pip install -r requirements.txt
```

## 使い方

`examples/basic_usage.py` を参照してください。

### WebView Agent I

```python
from agent_i import AgentIClient

client = AgentIClient()
for chunk in client.chat("こんにちは！"):
    if chunk.text:
        print(chunk.text, end="")
```

### Native LINE AI

```python
from agent_i import LineAiClient

client = LineAiClient(access_token="YOUR_CHANNEL_TOKEN")
client.submit_agreement()
thread = client.create_thread()

for chunk in client.query(thread_id=thread.body['result']['threadId'], message="元気？"):
    print(chunk.data)
```

## ライセンス
MIT License
