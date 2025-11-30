"""OAuth 2.0認証処理"""
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, urlparse, parse_qs
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import requests

from .config import config
from .logger import setup_logger
from .exceptions import AuthenticationError

logger = setup_logger(__name__)


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """OAuthコールバックを処理するHTTPハンドラー"""

    auth_code: Optional[str] = None
    error: Optional[str] = None

    def do_GET(self):
        """GETリクエストを処理"""
        # クエリパラメータを解析
        query = urlparse(self.path).query
        params = parse_qs(query)

        if 'code' in params:
            # 認証コード取得成功
            OAuthCallbackHandler.auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html = """
            <html>
            <head><title>認証完了</title></head>
            <body>
                <h1>認証が完了しました！</h1>
                <p>このウィンドウを閉じて、ターミナルに戻ってください。</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        elif 'error' in params:
            # エラー
            OAuthCallbackHandler.error = params['error'][0]
            self.send_response(400)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html = f"""
            <html>
            <head><title>認証エラー</title></head>
            <body>
                <h1>認証に失敗しました</h1>
                <p>エラー: {OAuthCallbackHandler.error}</p>
                <p>このウィンドウを閉じて、やり直してください。</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))

    def log_message(self, format, *args):
        """ログメッセージを抑制"""
        pass


class MoneyForwardAuth:
    """MoneyForward OAuth 2.0認証クライアント"""

    AUTH_URL = "https://invoice.moneyforward.com/oauth/authorize"
    TOKEN_URL = "https://invoice.moneyforward.com/oauth/token"
    TOKEN_FILE = Path.home() / ".notion-to-mf" / "mf_token.json"

    def __init__(self):
        """初期化"""
        self.client_id = config.MONEYFORWARD_CLIENT_ID
        self.client_secret = config.MONEYFORWARD_CLIENT_SECRET
        self.redirect_uri = config.MONEYFORWARD_REDIRECT_URI

        # トークンファイルのディレクトリを作成
        self.TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)

    def authenticate(self) -> Dict[str, Any]:
        """OAuth 2.0認証フローを実行

        Returns:
            トークン情報

        Raises:
            AuthenticationError: 認証に失敗した場合
        """
        try:
            config.validate_moneyforward()
        except ValueError as e:
            raise AuthenticationError(f"設定エラー: {e}")

        # 認証URLを生成
        auth_params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'write',  # MoneyForward請求書の書き込み権限
        }
        auth_url = f"{self.AUTH_URL}?{urlencode(auth_params)}"

        logger.info("ブラウザで認証ページを開きます...")
        logger.info(f"認証URL: {auth_url}")

        # ブラウザを開く
        webbrowser.open(auth_url)

        # ローカルサーバーを起動してコールバックを待機
        logger.info("認証コードを待機中...")
        port = int(self.redirect_uri.split(':')[-1].split('/')[0])

        server = HTTPServer(('localhost', port), OAuthCallbackHandler)
        server.handle_request()

        if OAuthCallbackHandler.error:
            raise AuthenticationError(f"認証エラー: {OAuthCallbackHandler.error}")

        if not OAuthCallbackHandler.auth_code:
            raise AuthenticationError("認証コードを取得できませんでした")

        # 認証コードをアクセストークンに交換
        logger.info("アクセストークンを取得中...")
        token_data = self._exchange_code_for_token(OAuthCallbackHandler.auth_code)

        # トークンを保存
        self._save_token(token_data)

        logger.info("認証が完了しました！")
        return token_data

    def _exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """認証コードをアクセストークンに交換

        Args:
            code: 認証コード

        Returns:
            トークン情報

        Raises:
            AuthenticationError: トークン取得に失敗した場合
        """
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }

        try:
            response = requests.post(self.TOKEN_URL, data=data)
            response.raise_for_status()
            token_data = response.json()

            # 有効期限を計算して追加
            if 'expires_in' in token_data:
                expires_at = datetime.now() + timedelta(seconds=token_data['expires_in'])
                token_data['expires_at'] = expires_at.isoformat()

            return token_data

        except requests.exceptions.RequestException as e:
            logger.error(f"トークン取得エラー: {e}")
            raise AuthenticationError(f"トークン取得に失敗しました: {e}")

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """リフレッシュトークンを使用してアクセストークンを更新

        Args:
            refresh_token: リフレッシュトークン

        Returns:
            新しいトークン情報

        Raises:
            AuthenticationError: トークン更新に失敗した場合
        """
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }

        try:
            response = requests.post(self.TOKEN_URL, data=data)
            response.raise_for_status()
            token_data = response.json()

            # 有効期限を計算して追加
            if 'expires_in' in token_data:
                expires_at = datetime.now() + timedelta(seconds=token_data['expires_in'])
                token_data['expires_at'] = expires_at.isoformat()

            # トークンを保存
            self._save_token(token_data)

            logger.info("アクセストークンを更新しました")
            return token_data

        except requests.exceptions.RequestException as e:
            logger.error(f"トークン更新エラー: {e}")
            raise AuthenticationError(f"トークン更新に失敗しました: {e}")

    def get_valid_token(self) -> Optional[str]:
        """有効なアクセストークンを取得

        Returns:
            アクセストークン（ない場合はNone）
        """
        token_data = self._load_token()
        if not token_data:
            return None

        # トークンの有効期限をチェック
        if 'expires_at' in token_data:
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            if datetime.now() >= expires_at:
                # トークンが期限切れ - リフレッシュを試みる
                if 'refresh_token' in token_data:
                    try:
                        token_data = self.refresh_token(token_data['refresh_token'])
                    except AuthenticationError:
                        return None
                else:
                    return None

        return token_data.get('access_token')

    def is_authenticated(self) -> bool:
        """認証済みかどうかを確認

        Returns:
            認証済みの場合True
        """
        return self.get_valid_token() is not None

    def _save_token(self, token_data: Dict[str, Any]) -> None:
        """トークンをファイルに保存

        Args:
            token_data: トークン情報
        """
        with open(self.TOKEN_FILE, 'w') as f:
            json.dump(token_data, f, indent=2)

        # ファイルのパーミッションを制限（Unix系のみ）
        try:
            self.TOKEN_FILE.chmod(0o600)
        except Exception:
            pass  # Windowsでは無視

        logger.debug(f"トークンを保存しました: {self.TOKEN_FILE}")

    def _load_token(self) -> Optional[Dict[str, Any]]:
        """トークンをファイルから読み込み

        Returns:
            トークン情報（ない場合はNone）
        """
        if not self.TOKEN_FILE.exists():
            return None

        try:
            with open(self.TOKEN_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"トークン読み込みエラー: {e}")
            return None

    def clear_token(self) -> None:
        """保存されているトークンを削除"""
        if self.TOKEN_FILE.exists():
            self.TOKEN_FILE.unlink()
            logger.info("トークンを削除しました")
