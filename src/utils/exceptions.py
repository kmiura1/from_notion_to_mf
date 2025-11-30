"""カスタム例外定義"""


class NotionToMFError(Exception):
    """基底例外クラス"""
    pass


class ConfigError(NotionToMFError):
    """設定エラー"""
    pass


class NotionAPIError(NotionToMFError):
    """Notion APIエラー"""
    pass


class MoneyForwardAPIError(NotionToMFError):
    """MoneyForward APIエラー"""
    pass


class DataValidationError(NotionToMFError):
    """データ検証エラー"""
    pass


class AuthenticationError(NotionToMFError):
    """認証エラー"""
    pass
