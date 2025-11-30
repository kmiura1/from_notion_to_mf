# from_notion_to_mf

Notionの研修案件データベースからデータを取得し、MoneyForwardの請求書として作成するCLIツール

## 機能

- Notionの「研修案件管理」データベースからデータを取得
- 複数の出力形式に対応（テーブル、詳細、JSON、CSV）
- ステータスフィルタリング
- MoneyForward請求書への転記（Phase 2以降で実装予定）

## セットアップ

### 1. 依存パッケージのインストール

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env`ファイルに以下の情報を設定：

```bash
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_database_id
```

## 使い方

### 基本的な使い方

```bash
# Notionから研修案件を取得して表示
python -m src fetch

# ステータスでフィルタ
python -m src fetch --status 完了

# 取得件数を制限
python -m src fetch --limit 10

# 詳細表示
python -m src fetch --format detailed

# JSON形式で出力
python -m src fetch --format json

# ファイルに出力
python -m src fetch --format json --output data.json
python -m src fetch --format csv --output data.csv
```

### コマンド一覧

```bash
# ヘルプを表示
python -m src --help

# バージョン情報
python -m src version
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
└── requirements.txt      # 依存パッケージ
```

## 開発状況

- [x] Phase 1: Notionデータ取得
- [ ] Phase 2: データエクスポート機能
- [ ] Phase 3: MoneyForward連携