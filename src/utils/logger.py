"""ロギング設定モジュール"""
import logging
import sys
from .config import config


def setup_logger(name: str = __name__) -> logging.Logger:
    """ロガーのセットアップ

    Args:
        name: ロガー名

    Returns:
        設定済みロガー
    """
    logger = logging.getLogger(name)

    # 既にハンドラが設定されている場合はスキップ
    if logger.handlers:
        return logger

    # ログレベル設定
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # コンソールハンドラ
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # フォーマット
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


# デフォルトロガー
logger = setup_logger('notion_to_mf')
