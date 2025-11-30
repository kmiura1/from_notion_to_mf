"""設定管理モジュール"""
import os
from pathlib import Path
from dotenv import load_dotenv

# .envファイルを読み込み
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """アプリケーション設定"""

    # Notion設定
    NOTION_API_KEY = os.getenv('NOTION_API_KEY')
    NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')

    # MoneyForward設定
    MONEYFORWARD_CLIENT_ID = os.getenv('MONEYFORWARD_CLIENT_ID')
    MONEYFORWARD_CLIENT_SECRET = os.getenv('MONEYFORWARD_CLIENT_SECRET')
    MONEYFORWARD_REDIRECT_URI = os.getenv('MONEYFORWARD_REDIRECT_URI', 'http://localhost:8080/callback')

    # アプリケーション設定
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    @classmethod
    def validate(cls):
        """必須設定の検証"""
        errors = []

        if not cls.NOTION_API_KEY:
            errors.append('NOTION_API_KEY が設定されていません')

        if not cls.NOTION_DATABASE_ID:
            errors.append('NOTION_DATABASE_ID が設定されていません')

        if errors:
            raise ValueError(f"設定エラー:\n" + "\n".join(f"  - {e}" for e in errors))

    @classmethod
    def validate_moneyforward(cls):
        """MoneyForward設定の検証"""
        errors = []

        if not cls.MONEYFORWARD_CLIENT_ID:
            errors.append('MONEYFORWARD_CLIENT_ID が設定されていません')

        if not cls.MONEYFORWARD_CLIENT_SECRET:
            errors.append('MONEYFORWARD_CLIENT_SECRET が設定されていません')

        if errors:
            raise ValueError(f"MoneyForward設定エラー:\n" + "\n".join(f"  - {e}" for e in errors))


config = Config()
