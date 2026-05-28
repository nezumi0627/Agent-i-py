"""
LINE AIクライアントのテスト
"""
import unittest
from unittest.mock import Mock, patch

from agent_i import (
    AgentIChunk,
    AgentIClient,
    AgentIConfig,
    AgentSource,
    ChatMessage,
    ContextType,
    LineAiClient,
    LineAiConfig,
    LineAiQueryChunk,
    LineAiResponse,
    RateLimitInfo,
    ThreadInfo,
)
from agent_i.exceptions import ApiError


class TestAgentIClient(unittest.TestCase):
    """AgentIClientのテスト"""
    
    def setUp(self):
        self.client = AgentIClient()
    
    @patch('agent_i.webview.requests.Session.get')
    def test_mint_anonymous_cookies(self, mock_get):
        """匿名クッキー取得のテスト"""
        mock_response = Mock()
        mock_response.headers.get.return_value = "B=anon-b-value; Path=/, XB=anon-xb-value; Path=/"
        mock_get.return_value = mock_response

        cookies = self.client.mint_anonymous_cookies()

        self.assertIn("B=anon-b-value", cookies)
        self.assertIn("XB=anon-xb-value", cookies)
        mock_get.assert_called_once()

    def test_build_webview_url(self):
        """build_webview_urlのテスト"""
        url = self.client.build_webview_url("こんにちは")
        self.assertIn("fr=line_agenti_chattab_searchbar", url)
        self.assertIn("frtype=line_chattab_searchbar", url)
        self.assertTrue("q=%E3%81%93%E3%82%93%E3%81%AB%E3%81%A1%E3%81%AF" in url or "q=こんにちは" in url)

    def test_extract_text(self):
        """extractTextのテスト"""
        # 文字列
        self.assertEqual(AgentIChunk._extract_text("hello"), "hello")

        # compositeMessage-delta形状
        data = {"type": "compositeMessage-delta", "value": {"message": "test"}}
        self.assertEqual(AgentIChunk._extract_text(data), "test")
        
        # compositeMessage-delta (dict message)
        data2 = {"type": "compositeMessage-delta", "value": {"message": {"text": "test2"}}}
        self.assertEqual(AgentIChunk._extract_text(data2), "test2")

        # textフィールド
        self.assertEqual(AgentIChunk._extract_text({"text": "hi"}), "hi")

        # deltaフィールド
        self.assertEqual(AgentIChunk._extract_text({"delta": "delta"}), "delta")

        # contents配列
        data = {"contents": [{"text": "hello"}, {"text": "world"}]}
        self.assertEqual(AgentIChunk._extract_text(data), "helloworld")
    
    @patch('agent_i.base.requests.Session.request')
    @patch.object(AgentIClient, 'mint_anonymous_cookies')
    def test_chat_with_auto_cookies(self, mock_mint, mock_request):
        """自動クッキー取得付きチャットのテスト"""
        mock_mint.return_value = 'B=test_b; XB=test_xb'
        
        mock_response = Mock()
        # requests のストリーミングモック
        mock_response.iter_content.return_value = iter([
            b'event: compositeMessage-delta\n',
            'data: {"type": "compositeMessage-delta", "value": {"message": "テスト応答"}}\n\n'.encode('utf-8'),
        ])
        mock_response.iter_lines.return_value = iter([
            b'event: compositeMessage-delta',
            'data: {"type": "compositeMessage-delta", "value": {"message": "テスト応答"}}'.encode('utf-8'),
            b'',
        ])
        mock_request.return_value = mock_response
        
        with patch('agent_i.webview.sseclient.SSEClient') as mock_sse:
            mock_event = Mock()
            mock_event.event = 'compositeMessage-delta'
            mock_event.data = '{"type": "compositeMessage-delta", "value": {"message": "テスト応答"}}'
            
            mock_sse_instance = Mock()
            mock_sse_instance.events.return_value = [mock_event]
            mock_sse.return_value = mock_sse_instance
            
            chunks = list(self.client.chat("こんにちは"))
            
            self.assertEqual(len(chunks), 1)
            self.assertEqual(chunks[0].text, 'テスト応答')


class TestLineAiClient(unittest.TestCase):
    """LineAiClientのテスト"""

    def setUp(self):
        self.client = LineAiClient(
            access_token="test_token",
            line_version="26.7.2"
        )

    def test_initialization(self):
        """初期化のテスト"""
        self.assertEqual(self.client.access_token, "test_token")
        self.assertEqual(self.client.line_version, "26.7.2")
        self.assertEqual(self.client.host, LineAiConfig.DEFAULT_HOST)

    @patch('agent_i.base.requests.Session.request')
    def test_get_service_info(self, mock_request):
        """サービス情報取得のテスト"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.text = '{"serviceInfo": "test"}'
        mock_response.headers = {}
        mock_request.return_value = mock_response

        result = self.client.get_service_info()

        self.assertEqual(result.body, {"serviceInfo": "test"})
        self.assertEqual(result.status, 200)

    @patch('agent_i.base.requests.Session.request')
    def test_create_thread(self, mock_request):
        """スレッド作成のテスト"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.text = '{"result": {"threadId": "test_thread_id", "encryptionKey": "test_key"}}'
        mock_response.headers = {}
        mock_request.return_value = mock_response

        result = self.client.create_thread()

        self.assertEqual(result.body["result"]["threadId"], "test_thread_id")


class TestIntegration(unittest.TestCase):
    """統合テスト（設定・データクラス検証）"""

    def test_constants(self):
        """定数のテスト"""
        self.assertEqual(LineAiConfig.CHANNEL_ID, "2006890580")
        self.assertEqual(LineAiConfig.DEFAULT_HOST, "https://line-x-openai.line-apps.com")
        self.assertEqual(AgentIConfig.DEFAULT_ENDPOINT, "https://search-agent.yahoo.co.jp/v2/chat")
        
        # Enums
        self.assertEqual(AgentSource.CHAT_TAB.frcode, "line_agenti_chattab_searchbar")

    def test_data_classes(self):
        """データクラスのテスト"""
        thread_info = ThreadInfo(threadId="test", encryptionKey="key")
        self.assertEqual(thread_info.threadId, "test")

        chat_msg = ChatMessage(id="id1", role="user", contents=[{"type": "text", "text": "hi"}])
        self.assertEqual(chat_msg.role, "user")

        chunk = AgentIChunk(event="message", data="test", text="test")
        self.assertEqual(chunk.event, "message")

        query_chunk = LineAiQueryChunk(event="run.started", data={"runId": "R1"})
        self.assertEqual(query_chunk.event, "run.started")

        response = LineAiResponse(status=200, rate_limit=RateLimitInfo(), body={"ok": True})
        self.assertEqual(response.status, 200)


if __name__ == '__main__':
    unittest.main()
