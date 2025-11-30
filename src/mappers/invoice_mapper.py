"""Notionデータから請求書への変換マッパー"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from ..models.training_project import TrainingProject
from ..models.invoice import Invoice, InvoiceItem
from ..utils.logger import setup_logger
from ..utils.exceptions import DataValidationError

logger = setup_logger(__name__)


class InvoiceMapper:
    """請求書データマッピングクラス"""

    def __init__(self, tax_rate: Decimal = Decimal("0.10")):
        """初期化

        Args:
            tax_rate: 消費税率（デフォルト: 10%）
        """
        self.tax_rate = tax_rate

    def map_to_invoice(
        self,
        project: TrainingProject,
        invoice_date: Optional[date] = None,
        payment_terms_days: int = 30
    ) -> Invoice:
        """研修案件を請求書に変換

        Args:
            project: 研修案件データ
            invoice_date: 請求日（指定なしの場合は研修終了日）
            payment_terms_days: 支払期限日数（デフォルト: 30日）

        Returns:
            請求書データ

        Raises:
            DataValidationError: データが不正な場合
        """
        # データ検証
        self._validate_project(project)

        # 請求日の決定
        if invoice_date is None:
            invoice_date = self._determine_invoice_date(project)

        # 支払期限の計算
        due_date = invoice_date + timedelta(days=payment_terms_days)

        # 明細行の作成
        items = self._create_invoice_items(project)

        # 小計の計算
        subtotal = sum(item.amount for item in items)

        # 消費税の計算
        tax_amount = (subtotal * self.tax_rate).quantize(Decimal("0"))

        # 合計金額
        total_amount = subtotal + tax_amount

        # 請求書作成
        invoice = Invoice(
            invoice_date=invoice_date,
            due_date=due_date,
            customer_name=project.customer_name or "顧客名未設定",
            customer_id=project.customer_id,
            items=items,
            subtotal=subtotal,
            tax_rate=self.tax_rate,
            tax_amount=tax_amount,
            total_amount=total_amount,
            notes=self._create_notes(project),
            source_id=project.id,
            project_name=project.title,
        )

        logger.info(f"請求書を作成しました: {project.title} - {total_amount:,.0f}円")
        return invoice

    def _validate_project(self, project: TrainingProject) -> None:
        """研修案件データの検証

        Args:
            project: 研修案件データ

        Raises:
            DataValidationError: データが不正な場合
        """
        errors = []

        if not project.title:
            errors.append("案件名が設定されていません")

        if project.amount is None or project.amount <= 0:
            errors.append(f"金額が不正です: {project.amount}")

        if not project.end_date:
            errors.append("研修終了日が設定されていません")

        if errors:
            error_msg = f"データ検証エラー ({project.title}):\n" + "\n".join(f"  - {e}" for e in errors)
            raise DataValidationError(error_msg)

    def _determine_invoice_date(self, project: TrainingProject) -> date:
        """請求日を決定

        Args:
            project: 研修案件データ

        Returns:
            請求日
        """
        # 研修終了日を請求日とする
        if project.end_date:
            return project.end_date.date()

        # 終了日がない場合は開始日
        if project.start_date:
            return project.start_date.date()

        # どちらもない場合は今日
        return date.today()

    def _create_invoice_items(self, project: TrainingProject) -> list[InvoiceItem]:
        """請求明細行を作成

        Args:
            project: 研修案件データ

        Returns:
            請求明細のリスト
        """
        items = []

        # メイン明細
        main_item = InvoiceItem(
            item_name=project.title,
            quantity=1,
            unit_price=Decimal(str(project.amount)),
            amount=Decimal(str(project.amount)),
            description=self._create_item_description(project),
        )
        items.append(main_item)

        return items

    def _create_item_description(self, project: TrainingProject) -> str:
        """明細の説明を作成

        Args:
            project: 研修案件データ

        Returns:
            説明文
        """
        parts = []

        if project.start_date and project.end_date:
            date_range = project.format_date_range()
            parts.append(f"実施期間: {date_range}")

        if project.participants:
            parts.append(f"参加人数: {project.participants}名")

        if project.days:
            parts.append(f"日数: {project.days}日")

        if project.location:
            parts.append(f"場所: {project.location}")

        if project.format:
            parts.append(f"形式: {project.format}")

        return " / ".join(parts) if parts else ""

    def _create_notes(self, project: TrainingProject) -> Optional[str]:
        """備考を作成

        Args:
            project: 研修案件データ

        Returns:
            備考
        """
        notes_parts = []

        if project.notes:
            notes_parts.append(project.notes)

        notes_parts.append(f"Notion案件ID: {project.id}")

        return "\n\n".join(notes_parts) if notes_parts else None

    def map_batch(
        self,
        projects: list[TrainingProject],
        skip_errors: bool = True
    ) -> tuple[list[Invoice], list[str]]:
        """複数の研修案件を一括変換

        Args:
            projects: 研修案件のリスト
            skip_errors: エラーをスキップするか

        Returns:
            (成功した請求書のリスト, エラーメッセージのリスト)
        """
        invoices = []
        errors = []

        for project in projects:
            try:
                invoice = self.map_to_invoice(project)
                invoices.append(invoice)
            except DataValidationError as e:
                error_msg = f"{project.title}: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"請求書作成をスキップ: {error_msg}")

                if not skip_errors:
                    raise

        logger.info(f"バッチ変換完了: {len(invoices)}件成功, {len(errors)}件エラー")
        return invoices, errors
