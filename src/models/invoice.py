"""請求書データモデル"""
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class InvoiceItem(BaseModel):
    """請求書明細行"""

    item_name: str = Field(..., description="品目名")
    quantity: int = Field(default=1, description="数量")
    unit_price: Decimal = Field(..., description="単価")
    amount: Decimal = Field(..., description="金額")
    description: Optional[str] = Field(None, description="説明")

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Decimal, info) -> Decimal:
        """金額の検証"""
        if v < 0:
            raise ValueError("金額は0以上である必要があります")
        return v


class Invoice(BaseModel):
    """請求書モデル（MoneyForward形式）"""

    # 基本情報
    invoice_number: Optional[str] = Field(None, description="請求書番号")
    invoice_date: date = Field(..., description="請求日")
    due_date: Optional[date] = Field(None, description="支払期限")

    # 顧客情報
    customer_name: str = Field(..., description="顧客名")
    customer_id: Optional[str] = Field(None, description="顧客ID")

    # 明細
    items: List[InvoiceItem] = Field(..., description="請求明細")

    # 金額情報
    subtotal: Decimal = Field(..., description="小計（税抜）")
    tax_rate: Decimal = Field(default=Decimal("0.10"), description="消費税率")
    tax_amount: Decimal = Field(..., description="消費税額")
    total_amount: Decimal = Field(..., description="合計（税込）")

    # メタ情報
    notes: Optional[str] = Field(None, description="備考")
    source_id: Optional[str] = Field(None, description="元データID (Notion)")
    project_name: Optional[str] = Field(None, description="プロジェクト名")

    class Config:
        """Pydantic設定"""
        json_encoders = {
            Decimal: lambda v: float(v),
            date: lambda v: v.isoformat() if v else None,
        }

    @field_validator('tax_amount', 'total_amount')
    @classmethod
    def validate_positive(cls, v: Decimal) -> Decimal:
        """正の数値を検証"""
        if v < 0:
            raise ValueError("金額は0以上である必要があります")
        return v

    def calculate_totals(self) -> None:
        """合計金額を再計算"""
        self.subtotal = sum(item.amount for item in self.items)
        self.tax_amount = (self.subtotal * self.tax_rate).quantize(Decimal("0"))
        self.total_amount = self.subtotal + self.tax_amount

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return self.model_dump(mode='json', exclude_none=True)

    def format_summary(self) -> str:
        """サマリーを整形"""
        lines = [
            f"請求書: {self.invoice_number or '未発行'}",
            f"顧客: {self.customer_name}",
            f"請求日: {self.invoice_date}",
            f"小計: {self.subtotal:,.0f}円（税抜）",
            f"消費税: {self.tax_amount:,.0f}円",
            f"合計: {self.total_amount:,.0f}円（税込）",
        ]
        return "\n".join(lines)
