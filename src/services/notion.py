"""Notion API連携サービス"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from notion_client import Client
from ..models.training_project import TrainingProject
from ..utils.config import config
from ..utils.logger import setup_logger
from ..utils.exceptions import NotionAPIError

logger = setup_logger(__name__)


class NotionService:
    """Notion API操作クラス"""

    def __init__(self):
        """初期化"""
        if not config.NOTION_API_KEY:
            raise NotionAPIError("NOTION_API_KEY が設定されていません")

        self.client = Client(auth=config.NOTION_API_KEY)
        self.database_id = config.NOTION_DATABASE_ID

    def fetch_training_projects(
        self,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None,
        start_date_from: Optional[str] = None,
        start_date_to: Optional[str] = None,
        amount_min: Optional[float] = None,
        amount_max: Optional[float] = None
    ) -> List[TrainingProject]:
        """研修案件を取得

        Args:
            status_filter: ステータスでフィルタ（受注/実施中/完了）
            limit: 取得件数の上限
            start_date_from: 開始日の下限 (YYYY-MM-DD)
            start_date_to: 開始日の上限 (YYYY-MM-DD)
            amount_min: 金額の下限
            amount_max: 金額の上限

        Returns:
            研修案件のリスト
        """
        try:
            logger.info(f"Notionデータベースから研修案件を取得中... (DB: {self.database_id})")

            # クエリ条件を構築
            query_params: Dict[str, Any] = {}
            filters = []

            # ステータスフィルタ
            if status_filter:
                filters.append({
                    "property": "ステータス",
                    "status": {
                        "equals": status_filter
                    }
                })

            # 開始日フィルタ
            if start_date_from:
                filters.append({
                    "property": "開始",
                    "date": {
                        "on_or_after": start_date_from
                    }
                })

            if start_date_to:
                filters.append({
                    "property": "開始",
                    "date": {
                        "on_or_before": start_date_to
                    }
                })

            # 金額フィルタ
            if amount_min is not None:
                filters.append({
                    "property": "金額",
                    "number": {
                        "greater_than_or_equal_to": amount_min
                    }
                })

            if amount_max is not None:
                filters.append({
                    "property": "金額",
                    "number": {
                        "less_than_or_equal_to": amount_max
                    }
                })

            # フィルタを結合
            if filters:
                if len(filters) == 1:
                    query_params["filter"] = filters[0]
                else:
                    query_params["filter"] = {
                        "and": filters
                    }

            if limit:
                query_params["page_size"] = min(limit, 100)

            # データベースをクエリ
            response = self.client.databases.query(
                database_id=self.database_id,
                **query_params
            )

            projects = []
            for page in response.get("results", []):
                try:
                    project = self._parse_page(page)
                    projects.append(project)
                except Exception as e:
                    logger.warning(f"ページの解析に失敗: {page.get('id')} - {e}")
                    continue

            logger.info(f"{len(projects)}件の研修案件を取得しました")
            return projects

        except Exception as e:
            logger.error(f"Notion APIエラー: {e}")
            raise NotionAPIError(f"データ取得に失敗しました: {e}")

    def _parse_page(self, page: Dict[str, Any]) -> TrainingProject:
        """NotionページをTrainingProjectに変換

        Args:
            page: Notion APIから返されたページデータ

        Returns:
            TrainingProject
        """
        props = page.get("properties", {})

        # タイトル取得
        title_prop = props.get("案件名", {})
        title = self._extract_title(title_prop)

        # ステータス取得
        status_prop = props.get("ステータス", {})
        status = self._extract_status(status_prop)

        # 日付取得
        start_prop = props.get("開始", {})
        end_prop = props.get("終了", {})
        start_date = self._extract_date(start_prop)
        end_date = self._extract_date(end_prop)

        # 顧客名取得（Relation）
        customer_prop = props.get("顧客名", {})
        customer_name, customer_id = self._extract_relation(customer_prop)

        # 金額取得
        amount_prop = props.get("金額", {})
        amount = self._extract_number(amount_prop)

        # その他の数値
        unit_price = self._extract_number(props.get("単価", {}))
        participants = self._extract_number(props.get("参加人数", {}))
        days = self._extract_number(props.get("日数", {}))

        # テキスト情報
        location = self._extract_text(props.get("研修場所", {}))
        format_type = self._extract_select(props.get("研修形式", {}))
        notes = self._extract_text(props.get("備考", {}))

        # メタ情報
        created_time = page.get("created_time")
        last_edited_time = page.get("last_edited_time")

        return TrainingProject(
            id=page["id"],
            title=title,
            status=status,
            start_date=self._parse_datetime(start_date) if start_date else None,
            end_date=self._parse_datetime(end_date) if end_date else None,
            customer_name=customer_name,
            customer_id=customer_id,
            amount=amount,
            unit_price=unit_price,
            participants=int(participants) if participants else None,
            days=int(days) if days else None,
            location=location,
            format=format_type,
            notes=notes,
            created_time=self._parse_datetime(created_time) if created_time else None,
            last_edited_time=self._parse_datetime(last_edited_time) if last_edited_time else None,
        )

    def _extract_title(self, prop: Dict[str, Any]) -> str:
        """タイトルプロパティから値を抽出"""
        if prop.get("type") == "title":
            title_items = prop.get("title", [])
            if title_items:
                return "".join([item.get("plain_text", "") for item in title_items])
        return "無題"

    def _extract_status(self, prop: Dict[str, Any]) -> Optional[str]:
        """ステータスプロパティから値を抽出"""
        if prop.get("type") == "status":
            status_obj = prop.get("status")
            if status_obj:
                return status_obj.get("name")
        return None

    def _extract_date(self, prop: Dict[str, Any]) -> Optional[str]:
        """日付プロパティから値を抽出"""
        if prop.get("type") == "date":
            date_obj = prop.get("date")
            if date_obj:
                return date_obj.get("start")
        return None

    def _extract_relation(self, prop: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
        """リレーションプロパティから値を抽出（名前とIDのタプル）"""
        if prop.get("type") == "relation":
            relations = prop.get("relation", [])
            if relations:
                # 最初のリレーションのIDを取得
                relation_id = relations[0].get("id")
                # TODO: 実際の顧客名を取得するには、関連ページを取得する必要がある
                # 今は簡易実装として、IDのみ保存
                return None, relation_id
        return None, None

    def _extract_number(self, prop: Dict[str, Any]) -> Optional[float]:
        """数値プロパティから値を抽出"""
        if prop.get("type") == "number":
            return prop.get("number")
        return None

    def _extract_text(self, prop: Dict[str, Any]) -> Optional[str]:
        """テキストプロパティから値を抽出"""
        if prop.get("type") == "rich_text":
            texts = prop.get("rich_text", [])
            if texts:
                return "".join([item.get("plain_text", "") for item in texts])
        return None

    def _extract_select(self, prop: Dict[str, Any]) -> Optional[str]:
        """セレクトプロパティから値を抽出"""
        if prop.get("type") == "select":
            select_obj = prop.get("select")
            if select_obj:
                return select_obj.get("name")
        return None

    def _parse_datetime(self, dt_str: str) -> datetime:
        """ISO8601形式の日時文字列をdatetimeに変換"""
        try:
            # ISO8601形式をパース
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except Exception as e:
            logger.warning(f"日時のパースに失敗: {dt_str} - {e}")
            return datetime.now()

    def fetch_customer_name(self, customer_id: str) -> Optional[str]:
        """顧客IDから顧客名を取得

        Args:
            customer_id: 顧客ページのID

        Returns:
            顧客名
        """
        try:
            page = self.client.pages.retrieve(page_id=customer_id)
            props = page.get("properties", {})

            # 顧客マスタのタイトルを取得
            # プロパティ名は実際のデータベース構造に応じて調整が必要
            for key, value in props.items():
                if value.get("type") == "title":
                    return self._extract_title(value)

            return None

        except Exception as e:
            logger.warning(f"顧客名の取得に失敗: {customer_id} - {e}")
            return None
