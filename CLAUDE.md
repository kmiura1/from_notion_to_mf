# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Notionのデータベースからマネーフォワードの請求書に転記するためのプログラム。 
それぞれのAPIを使用する。 

## **研修案件管理** データベース（データソース: 研修の案件）のプロパティ一覧です。
https://www.notion.so/310735dca908424690146e780f0b0446/ds/139fdd5f99684704a2a829550ab8df29?db=5ef95ba6d8bd490ea6c226cdcbfcc261&source=copy_link

1. **案件名**（title）
2. **ステータス**（status）
    - 受注 / 実施中 / 完了
3. **開始**（date）
    - 研修開始日時
4. **終了**（date）
    - 研修終了日時
5. **顧客名**（relation → 顧客マスタ [顧客](https://www.notion.so/310735dca908424690146e780f0b0446/ds/304b4d2ca43c4d2cba38f648856888f5?db=87911d8cefbb43449de44b454e3c4efd&pvs=21)）
6. **金額**（number, 円・税抜・0桁）
    - 契約金額（税抜）
7. **単価**（number, カンマ区切り）
8. **参加人数**（number, 0桁・バー表示, max 100）
9. **日数**（number, 0桁）
10. **研修場所**（text）
11. **研修形式**（select）
    - オンライン / オフライン / ハイブリッド
12. **📄 注文書**（relation → 注文書 [注文書](https://www.notion.so/310735dca908424690146e780f0b0446/ds/d9cf5280a7c242c6bc7e175c0acfaa82?db=eece47ad249449cc9a8bf3a8ac109e7b&pvs=21)）
13. **🧑🏻‍🎓 研修の記録**（relation → 研修の記録 [研修の記録](https://www.notion.so/310735dca908424690146e780f0b0446/ds/3820f4c0e4f44bdfb0b469c96a948097?db=4e44355f1a57400ab439312697a75133&pvs=21)）
14. **備考**（text）
15. **作成日時**（created_time）
16. **最終更新日時**（last_edited_time）

## API情報

### Notion API
- APIドキュメント: https://developers.notion.com/
- 認証方式: Integration Token
- 必要な権限: データベース読み取り
- **認証情報は `.env` ファイルで管理してください**

### マネーフォワード請求書API
- APIドキュメント: https://invoice.moneyforward.com/docs/api/v3/index.html#/
- 認証方式: OAuth 2.0 (CLIENT_SECRET_BASIC)
- リダイレクトURI: http://localhost:8080/callback
- **認証情報は `.env` ファイルで管理してください**


## Current State

CLAUDE.mdに追加するアーキテクチャ案を提示します。askモードのため直接編集はできませんが、以下をコピーして適用してください。


[1 tool called]


アーキテクチャ案を `CLAUDE.md` に追加しました。以下をファイルにコピーしてください。

```markdown:CLAUDE.md
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Notionのデータベースからマネーフォワードの請求書に転記するためのプログラム。 
それぞれのAPIを使用する。 


## Architecture Design

### 技術スタック

- **言語**: Python 3.13+
- **主要ライブラリ**:
  - `notion-client`: Notion API公式クライアント
  - `requests`: HTTP通信（マネーフォワード API連携用）
  - `python-dotenv`: 環境変数管理
  - `pydantic`: データバリデーション
  - `logging`: ログ管理

### アーキテクチャ構成

```
┌─────────────────────────────────────────────────────────────┐
│                    アプリケーション層                         │
├─────────────────────────────────────────────────────────────┤
│  Main (CLI/API) → Orchestrator (Workflow) → Logger          │
├─────────────────────────────────────────────────────────────┤
│                      データ取得層                             │
├─────────────────────────────────────────────────────────────┤
│  NotionService                                               │
│  - connect()                                                 │
│  - fetch_database()                                          │
│  - query_training_projects()                                 │
│  - transform_notion_data()                                   │
├─────────────────────────────────────────────────────────────┤
│                      データ変換層                             │
├─────────────────────────────────────────────────────────────┤
│  DataMapper                                                  │
│  - map_notion_to_invoice()                                   │
│  - validate_invoice_data()                                   │
│  - calculate_amounts()                                       │
│  - format_invoice_fields()                                   │
│                                                               │
│  InvoiceModel (Pydantic)                                     │
│  - customer_name, invoice_date, items[], total_amount        │
├─────────────────────────────────────────────────────────────┤
│                      データ送信層                             │
├─────────────────────────────────────────────────────────────┤
│  MoneyForwardService                                         │
│  - authenticate()                                            │
│  - create_invoice()                                          │
│  - update_invoice()                                          │
│  - handle_api_response()                                     │
├─────────────────────────────────────────────────────────────┤
│                      設定・ユーティリティ層                   │
├─────────────────────────────────────────────────────────────┤
│  Config | Logger | Errors | Utils                            │
└─────────────────────────────────────────────────────────────┘
```

### ディレクトリ構造

```
from_notion_to_mf/
├── src/
│   ├── __init__.py
│   ├── main.py                 # エントリーポイント
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── notion_service.py   # Notion API連携
│   │   └── moneyforward_service.py  # マネーフォワード API連携
│   │
│   ├── mappers/
│   │   ├── __init__.py
│   │   └── invoice_mapper.py   # データ変換ロジック
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── notion_models.py    # Notionデータ構造
│   │   └── invoice_models.py   # 請求書データ構造
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py           # 設定管理
│   │   ├── logger.py           # ログ設定
│   │   └── exceptions.py       # カスタム例外
│   │
│   └── orchestrator/
│       ├── __init__.py
│       └── workflow.py         # ワークフロー制御
│
├── tests/
│   ├── __init__.py
│   ├── test_notion_service.py
│   ├── test_mapper.py
│   └── test_moneyforward_service.py
│
├── .env.example                # 環境変数テンプレート
├── .gitignore
├── requirements.txt            # 依存パッケージ
├── README.md
└── CLAUDE.md
```

### 実装の流れ

1. **初期化・認証**
   - 環境変数から認証情報を読み込み（NOTION_API_TOKEN, MONEYFORWARD_API_KEY, NOTION_DATABASE_ID）

2. **データ取得フェーズ**
   - Notion APIで「研修案件管理」データベースをクエリ
   - 必要なフィールドを抽出（案件名、金額、日付、顧客情報など）
   - データの検証とクレンジング

3. **データ変換フェーズ**
   - Notionデータを請求書形式にマッピング
     - 案件情報 → 請求書明細
     - 顧客情報 → 請求先
     - 金額・日付のフォーマット変換
   - 必須項目の検証
   - 金額計算（税額、合計など）

4. **データ送信フェーズ**
   - マネーフォワード APIで請求書を作成/更新
   - レスポンスの検証
   - エラーハンドリング

5. **ログ・監視**
   - 処理状況のログ記録
   - エラー時の通知
   - 成功/失敗の記録

### 重要な考慮事項

- **セキュリティ**: 認証情報は環境変数で管理（`.env`ファイル、`.gitignore`に追加）
- **エラーハンドリング**: リトライ機構、部分失敗時のロールバック、詳細なエラーログ
- **データ整合性**: マッピングルールの明確化、データ検証（Pydantic使用）
- **拡張性**: 他のデータソースへの対応、バッチ処理対応、スケジューリング対応

### 実装の優先順位

1. 環境構築（Python仮想環境、requirements.txt、.env.example）
2. Notion API接続とテスト
3. データマッピング仕様の定義
4. データ変換ロジックの実装
5. マネーフォワード API連携
6. エラーハンドリングとログ機能の追加
```

