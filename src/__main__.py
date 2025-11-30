"""パッケージをモジュールとして実行するためのエントリーポイント

使用方法:
    python -m src
"""
from .cli.commands import cli

if __name__ == '__main__':
    cli()
