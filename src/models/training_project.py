"""研修案件データモデル"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class TrainingProject(BaseModel):
    """研修案件モデル"""

    # Notion内部ID
    id: str = Field(..., description="Notion Page ID")

    # 基本情報
    title: str = Field(..., description="案件名")
    status: Optional[str] = Field(None, description="ステータス: 受注/実施中/完了")

    # 日時
    start_date: Optional[datetime] = Field(None, description="開始日時")
    end_date: Optional[datetime] = Field(None, description="終了日時")

    # 顧客情報
    customer_name: Optional[str] = Field(None, description="顧客名")
    customer_id: Optional[str] = Field(None, description="顧客ID (Notion)")

    # 金額情報
    amount: Optional[float] = Field(None, description="金額（税抜）")
    unit_price: Optional[float] = Field(None, description="単価")
    participants: Optional[int] = Field(None, description="参加人数")
    days: Optional[int] = Field(None, description="日数")

    # 研修詳細
    location: Optional[str] = Field(None, description="研修場所")
    format: Optional[str] = Field(None, description="研修形式: オンライン/オフライン/ハイブリッド")

    # メタ情報
    notes: Optional[str] = Field(None, description="備考")
    created_time: Optional[datetime] = Field(None, description="作成日時")
    last_edited_time: Optional[datetime] = Field(None, description="最終更新日時")

    # 関連情報（今後実装）
    order_form_ids: List[str] = Field(default_factory=list, description="注文書ID")
    training_record_ids: List[str] = Field(default_factory=list, description="研修記録ID")

    class Config:
        """Pydantic設定"""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return self.model_dump(mode='json', exclude_none=True)

    def format_amount(self) -> str:
        """金額をフォーマット"""
        if self.amount is None:
            return "0円"
        return f"{self.amount:,.0f}円"

    def format_date_range(self) -> str:
        """日付範囲をフォーマット"""
        if not self.start_date:
            return "未設定"

        start_str = self.start_date.strftime("%Y-%m-%d")

        if self.end_date and self.end_date != self.start_date:
            end_str = self.end_date.strftime("%Y-%m-%d")
            return f"{start_str} 〜 {end_str}"

        return start_str
