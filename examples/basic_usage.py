"""LINE AI クライアントの使用例"""
import os
from dotenv import load_dotenv

load_dotenv()

from agent_i import AgentIClient, LineAiClient, LineAiError


def example_webview_agent():
    """WebViewパスの使用例（Yahooクッキー使用）"""
    print("=== WebView Agent I Example ===")
    
    client = AgentIClient()
    message = "こんにちは"
    print(f"送信: {message}")

    try:
        print("応答:")
        full_response = ""
        for chunk in client.chat(message):
            if chunk.text:
                full_response += chunk.text
                print(f"  {chunk.event}: {chunk.text}")
        
        print(f"\\n完全な応答: {full_response}")
        print(f"\\n会話履歴: {len(client.history)} ターン")
        for msg in client.history:
            print(f"  {msg.role}: {msg.contents[0]['text'][:30]}...")

    except LineAiError as e:
        print(f"エラー: {e}")


def example_native_line_ai():
    """ネイティブLINE AIの使用例
    .env ファイルからトークンを読み込みます。
    """
    print("\\n=== Native LINE AI Example ===")
    
    # 抽出したトークン
    channel_token = os.environ.get("LINE_AI_CHANNEL_TOKEN")
    line_version = os.environ.get("LINE_VERSION", "26.7.2")
    
    if not channel_token:
        print("環境変数 LINE_AI_CHANNEL_TOKEN が設定されていません。")
        print(".env ファイルを作成するか、環境変数を設定してください。")
        return
        
    try:
        client = LineAiClient(access_token=channel_token, line_version=line_version)
        
        # サービス情報
        print("サービス情報を取得中...")
        service_response = client.get_service_info()
        print(f"Service Info Status: {service_response.status}")
        
        # 利用規約に同意
        print("\\n利用規約に同意中...")
        client.submit_agreement()

        # スレッド作成
        print("\\nスレッドを作成中...")
        thread_response = client.create_thread()
        if not thread_response.is_success:
            print(f"Failed to create thread: {thread_response.body}")
            return
            
        thread_id = thread_response.body.get('result', {}).get('threadId')
        if not thread_id:
            print(f"Thread ID not found in response: {thread_response.body}")
            return
        print(f"Thread ID: {thread_id}")

        # クエリ実行
        message = "Pythonのリスト内包表記について1行で教えて。"
        print(f"\\n送信: {message}")
        
        response_chunks = client.query(thread_id=thread_id, message=message)
        print("応答:")
        for chunk in response_chunks:
            # チャンクデータを表示
            print(f"  {chunk.event}: {chunk.data}")
            
        # スレッド削除
        print("\\nスレッドを削除中...")
        client.delete_thread(thread_id)
        print("Thread deleted")

    except LineAiError as e:
        print(f"エラー: {e}")


if __name__ == "__main__":
    example_webview_agent()
    print("\\n" + "="*50)
    example_native_line_ai()
