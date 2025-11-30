"""MoneyForward API連携サービス"""
from typing import Dict, Any, List, Optional
from decimal import Decimal
import requests

from ..models.invoice import Invoice
from ..utils.auth import MoneyForwardAuth
from ..utils.logger import setup_logger
from ..utils.exceptions import MoneyForwardAPIError, AuthenticationError

logger = setup_logger(__name__)


class MoneyForwardService:
    """MoneyForward API操作クライアント"""

    API_BASE_URL = "https://invoice.moneyforward.com/api/v3"

    def __init__(self):
        """初期化"""
        self.auth = MoneyForwardAuth()
        self._access_token: Optional[str] = None

    def _ensure_authenticated(self) -> None:
        """認証済みかどうかを確認

        Raises:
            AuthenticationError: 認証されていない場合
        """
        self._access_token = self.auth.get_valid_token()
        if not self._access_token:
            raise AuthenticationError(
                "MoneyForwardに認証されていません。\n"
                "まず 'python -m src auth' コマンドを実行してください。"
            )

    def _get_headers(self) -> Dict[str, str]:
        """APIリクエストヘッダーを取得

        Returns:
            ヘッダー辞書
        """
        return {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def create_invoice(self, invoice: Invoice) -> Dict[str, Any]:
        """請求書を作成

        Args:
            invoice: 請求書データ

        Returns:
            作成された請求書のレスポンス

        Raises:
            MoneyForwardAPIError: API呼び出しに失敗した場合
        """
        self._ensure_authenticated()

        # MoneyForward API形式に変換
        invoice_data = self._convert_to_mf_format(invoice)

        url = f"{self.API_BASE_URL}/billings"

        try:
            logger.info(f"請求書を作成中: {invoice.project_name}")
            response = requests.post(
                url,
                json=invoice_data,
                headers=self._get_headers()
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"請求書を作成しました: ID={result.get('id')}")
            return result

        except requests.exceptions.HTTPError as e:
            error_msg = self._extract_error_message(e.response)
            logger.error(f"請求書作成エラー: {error_msg}")
            raise MoneyForwardAPIError(f"請求書作成に失敗しました: {error_msg}")

        except requests.exceptions.RequestException as e:
            logger.error(f"API呼び出しエラー: {e}")
            raise MoneyForwardAPIError(f"API呼び出しに失敗しました: {e}")

    def get_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """請求書を取得

        Args:
            invoice_id: 請求書ID

        Returns:
            請求書データ

        Raises:
            MoneyForwardAPIError: API呼び出しに失敗した場合
        """
        self._ensure_authenticated()

        url = f"{self.API_BASE_URL}/billings/{invoice_id}"

        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"請求書取得エラー: {e}")
            raise MoneyForwardAPIError(f"請求書取得に失敗しました: {e}")

    def list_invoices(
        self,
        page: int = 1,
        per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """請求書一覧を取得

        Args:
            page: ページ番号
            per_page: 1ページあたりの件数

        Returns:
            請求書のリスト

        Raises:
            MoneyForwardAPIError: API呼び出しに失敗した場合
        """
        self._ensure_authenticated()

        url = f"{self.API_BASE_URL}/billings"
        params = {
            'page': page,
            'per_page': per_page,
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()
            result = response.json()
            return result.get('data', [])

        except requests.exceptions.RequestException as e:
            logger.error(f"請求書一覧取得エラー: {e}")
            raise MoneyForwardAPIError(f"請求書一覧取得に失敗しました: {e}")

    def _convert_to_mf_format(self, invoice: Invoice) -> Dict[str, Any]:
        """InvoiceオブジェクトをMoneyForward API形式に変換

        Args:
            invoice: 請求書データ

        Returns:
            MoneyForward API形式の辞書
        """
        # 明細行を変換
        items = []
        for item in invoice.items:
            items.append({
                'name': item.item_name,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'description': item.description or '',
                'excise': 'ten_percent',  # 消費税10%
            })

        # 請求書データを構築
        billing_data = {
            'billing': {
                'billing_date': invoice.invoice_date.isoformat(),
                'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
                'billing_number': invoice.invoice_number or '',
                'note': invoice.notes or '',
                'items': items,
            }
        }

        # 顧客情報（必要に応じて追加）
        if invoice.customer_name and invoice.customer_name != "顧客名未設定":
            billing_data['billing']['partner_name'] = invoice.customer_name

        return billing_data

    def _extract_error_message(self, response: requests.Response) -> str:
        """エラーレスポンスからメッセージを抽出

        Args:
            response: レスポンスオブジェクト

        Returns:
            エラーメッセージ
        """
        try:
            error_data = response.json()
            if 'errors' in error_data:
                errors = error_data['errors']
                if isinstance(errors, list):
                    return ', '.join(str(e) for e in errors)
                elif isinstance(errors, dict):
                    messages = []
                    for field, msgs in errors.items():
                        if isinstance(msgs, list):
                            messages.append(f"{field}: {', '.join(msgs)}")
                        else:
                            messages.append(f"{field}: {msgs}")
                    return ', '.join(messages)
                else:
                    return str(errors)
            elif 'error' in error_data:
                return str(error_data['error'])
            else:
                return response.text
        except Exception:
            return response.text

    def test_connection(self) -> bool:
        """API接続をテスト

        Returns:
            接続成功の場合True
        """
        try:
            self._ensure_authenticated()
            # 請求書一覧を1件取得して接続確認
            self.list_invoices(per_page=1)
            logger.info("MoneyForward API接続成功")
            return True
        except Exception as e:
            logger.error(f"MoneyForward API接続失敗: {e}")
            return False
