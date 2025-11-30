# from_notion_to_mf

Notionの研修案件データベースからデータを取得し、MoneyForwardの請求書として作成するCLIツール

## 機能

- Notionの「研修案件管理」データベースからデータを取得
- 複数の出力形式に対応（テーブル、詳細、JSON、CSV）
- ステータスフィルタリング
- MoneyForward請求書への転記（Phase 2以降で実装予定）

## セットアップ

### 1. uvのインストール

このプロジェクトは **uv** を使用したモダンなPythonプロジェクト管理を採用しています。

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 依存パッケージのインストール

```bash
# 依存関係のインストール
uv sync

# 開発依存関係も含めてインストール
uv sync --all-extras
```

### 3. 環境変数の設定

`.env`ファイルに以下の情報を設定：

```bash
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_database_id
```

## 使い方

### 基本的な使い方

```bash
# Notionから研修案件を取得して表示
uv run python -m src.main fetch
# または
uv run notion-to-mf fetch

# ステータスでフィルタ
uv run notion-to-mf fetch --status 完了

# 取得件数を制限
uv run notion-to-mf fetch --limit 10

# 詳細表示
uv run notion-to-mf fetch --format detailed

# JSON形式で出力
uv run notion-to-mf fetch --format json

# ファイルに出力
uv run notion-to-mf fetch --format json --output data.json
uv run notion-to-mf fetch --format csv --output data.csv
```

### コマンド一覧

```bash
# ヘルプを表示
uv run notion-to-mf --help

# バージョン情報
uv run notion-to-mf version
```

## プロジェクト構造

```
from_notion_to_mf/
├── src/
│   ├── cli/              # CLIコマンド
│   ├── services/         # API連携
│   ├── models/           # データモデル
│   ├── mappers/          # データ変換
│   └── utils/            # ユーティリティ
├── tests/                # テスト
├── .env                  # 環境変数（要作成）
├── .env.example          # 環境変数テンプレート
├── pyproject.toml        # プロジェクト設定・依存関係
└── uv.lock               # ロックファイル（自動生成）
```

## 開発状況

- [x] Phase 1: Notionデータ取得
- [ ] Phase 2: データエクスポート機能
- [ ] Phase 3: MoneyForward連携