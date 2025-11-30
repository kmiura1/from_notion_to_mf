"""CLIコマンド定義"""
import click
from typing import Optional
from decimal import Decimal
from ..services.notion import NotionService
from ..services.moneyforward import MoneyForwardService
from ..mappers.invoice_mapper import InvoiceMapper
from ..utils.config import config
from ..utils.auth import MoneyForwardAuth
from ..utils.exceptions import NotionToMFError, AuthenticationError
from . import formatters


@click.group()
@click.version_option(version="0.1.0", prog_name="notion-to-mf")
def cli():
    """Notion to MoneyForward 請求書転記ツール

    Notionの研修案件データベースからデータを取得し、
    MoneyForwardの請求書として作成するCLIツールです。
    """
    pass


@cli.command()
@click.option(
    '--status',
    type=click.Choice(['受注', '実施中', '完了'], case_sensitive=False),
    help='ステータスでフィルタ'
)
@click.option(
    '--limit',
    type=int,
    help='取得件数の上限'
)
@click.option(
    '--year',
    type=int,
    help='西暦で絞り込み (例: 2025)'
)
@click.option(
    '--month',
    type=int,
    help='月で絞り込み (1-12)'
)
@click.option(
    '--date-from',
    type=str,
    help='開始日の下限 (YYYY-MM-DD)'
)
@click.option(
    '--date-to',
    type=str,
    help='開始日の上限 (YYYY-MM-DD)'
)
@click.option(
    '--amount-min',
    type=float,
    help='金額の下限'
)
@click.option(
    '--amount-max',
    type=float,
    help='金額の上限'
)
@click.option(
    '--format',
    'output_format',
    type=click.Choice(['table', 'detailed', 'json', 'csv'], case_sensitive=False),
    default='table',
    help='出力形式 (デフォルト: table)'
)
@click.option(
    '--output',
    type=click.Path(),
    help='出力先ファイル（指定しない場合は標準出力）'
)
def fetch(
    status: Optional[str],
    limit: Optional[int],
    year: Optional[int],
    month: Optional[int],
    date_from: Optional[str],
    date_to: Optional[str],
    amount_min: Optional[float],
    amount_max: Optional[float],
    output_format: str,
    output: Optional[str]
):
    """Notionから研修案件を取得して表示

    \b
    例:
        notion-to-mf fetch
        notion-to-mf fetch --status 完了
        notion-to-mf fetch --year 2025 --month 1
        notion-to-mf fetch --format json --output data.json
        notion-to-mf fetch --limit 10 --format detailed
    """
    try:
        # 設定検証
        config.validate()

        # 年月フィルタをdate_from/date_toに変換
        if year or month:
            from datetime import date as date_type
            import calendar

            # 年が指定されていない場合は現在の年
            if not year:
                year = date_type.today().year

            # 月が指定されている場合は該当月のみ
            if month:
                if month < 1 or month > 12:
                    formatters.print_error("月は1-12の範囲で指定してください")
                    raise click.Abort()

                # 該当月の初日と末日
                _, last_day = calendar.monthrange(year, month)
                date_from = f"{year:04d}-{month:02d}-01"
                date_to = f"{year:04d}-{month:02d}-{last_day:02d}"
            else:
                # 月が指定されていない場合は該当年の全体
                date_from = f"{year:04d}-01-01"
                date_to = f"{year:04d}-12-31"

        # Notionサービス初期化
        notion = NotionService()

        # データ取得
        formatters.print_info("Notionからデータを取得中...")
        projects = notion.fetch_training_projects(
            status_filter=status,
            limit=limit,
            start_date_from=date_from,
            start_date_to=date_to,
            amount_min=amount_min,
            amount_max=amount_max
        )

        if not projects:
            formatters.print_warning("データが見つかりませんでした")
            return

        # フォーマットに応じて出力
        if output_format == 'table':
            formatters.format_table(projects)

        elif output_format == 'detailed':
            formatters.format_detailed(projects)

        elif output_format == 'json':
            json_output = formatters.format_json(projects)
            if output:
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(json_output)
                formatters.print_success(f"JSONファイルを出力しました: {output}")
            else:
                # UTF-8 で出力
                import sys
                if sys.platform == 'win32':
                    import io
                    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
                click.echo(json_output)

        elif output_format == 'csv':
            csv_output = formatters.format_csv(projects)
            if output:
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(csv_output)
                formatters.print_success(f"CSVファイルを出力しました: {output}")
            else:
                # UTF-8 で出力
                import sys
                if sys.platform == 'win32':
                    import io
                    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
                click.echo(csv_output)

    except NotionToMFError as e:
        formatters.print_error(f"エラー: {e}")
        raise click.Abort()

    except Exception as e:
        formatters.print_error(f"予期しないエラー: {e}")
        raise click.Abort()


@cli.command()
@click.option(
    '--status',
    type=click.Choice(['受注', '実施中', '完了'], case_sensitive=False),
    help='ステータスでフィルタ'
)
@click.option(
    '--year',
    type=int,
    help='西暦で絞り込み (例: 2025)'
)
@click.option(
    '--month',
    type=int,
    help='月で絞り込み (1-12)'
)
@click.option(
    '--date-from',
    type=str,
    help='開始日の下限 (YYYY-MM-DD)'
)
@click.option(
    '--date-to',
    type=str,
    help='開始日の上限 (YYYY-MM-DD)'
)
@click.option(
    '--amount-min',
    type=float,
    help='金額の下限'
)
@click.option(
    '--amount-max',
    type=float,
    help='金額の上限'
)
@click.option(
    '--grouped',
    is_flag=True,
    help='顧客×月でグループ化して請求書を作成'
)
@click.option(
    '--output',
    type=click.Path(),
    required=True,
    help='出力先ファイル（JSON形式）'
)
@click.option(
    '--skip-errors',
    is_flag=True,
    default=True,
    help='エラーをスキップして処理を継続'
)
@click.option(
    '--show-stats',
    is_flag=True,
    default=True,
    help='統計情報を表示'
)
def export(
    status: Optional[str],
    year: Optional[int],
    month: Optional[int],
    date_from: Optional[str],
    date_to: Optional[str],
    amount_min: Optional[float],
    amount_max: Optional[float],
    grouped: bool,
    output: str,
    skip_errors: bool,
    show_stats: bool
):
    """研修案件を請求書形式でエクスポート

    \b
    例:
        notion-to-mf export --output invoices.json
        notion-to-mf export --status 完了 --output completed.json
        notion-to-mf export --year 2025 --month 1 --grouped --output 2025-01.json
        notion-to-mf export --date-from 2025-01-01 --date-to 2025-03-31 --output q1.json
        notion-to-mf export --amount-min 100000 --output large-projects.json
    """
    try:
        # 設定検証
        config.validate()

        # 年月フィルタをdate_from/date_toに変換
        if year or month:
            from datetime import date as date_type
            import calendar

            # 年が指定されていない場合は現在の年
            if not year:
                year = date_type.today().year

            # 月が指定されている場合は該当月のみ
            if month:
                if month < 1 or month > 12:
                    formatters.print_error("月は1-12の範囲で指定してください")
                    raise click.Abort()

                # 該当月の初日と末日
                _, last_day = calendar.monthrange(year, month)
                date_from = f"{year:04d}-{month:02d}-01"
                date_to = f"{year:04d}-{month:02d}-{last_day:02d}"
            else:
                # 月が指定されていない場合は該当年の全体
                date_from = f"{year:04d}-01-01"
                date_to = f"{year:04d}-12-31"

        # サービス初期化
        notion = NotionService()
        mapper = InvoiceMapper()

        # データ取得
        formatters.print_info("Notionからデータを取得中...")
        projects = notion.fetch_training_projects(
            status_filter=status,
            start_date_from=date_from,
            start_date_to=date_to,
            amount_min=amount_min,
            amount_max=amount_max
        )

        if not projects:
            formatters.print_warning("データが見つかりませんでした")
            return

        formatters.print_info(f"{len(projects)}件の研修案件を取得しました")

        # 請求書に変換（グループ化オプションに応じて）
        if grouped:
            formatters.print_info("顧客×月でグループ化して請求書形式に変換中...")
            invoices, errors = mapper.map_grouped_invoices(projects, skip_errors=skip_errors)
        else:
            formatters.print_info("請求書形式に変換中...")
            invoices, errors = mapper.map_batch(projects, skip_errors=skip_errors)

        if errors:
            formatters.print_warning(f"{len(errors)}件のエラーがありました:")
            for error in errors:
                formatters.print_error(f"  - {error}")

        if not invoices:
            formatters.print_error("有効な請求書を作成できませんでした")
            raise click.Abort()

        # 統計情報の計算
        if show_stats:
            total_amount = sum(invoice.total_amount for invoice in invoices)
            total_tax = sum(invoice.tax_amount for invoice in invoices)
            total_subtotal = sum(invoice.subtotal for invoice in invoices)

            formatters.print_info("\n=== 統計情報 ===")
            click.echo(f"請求書件数: {len(invoices)}件")
            click.echo(f"小計: {total_subtotal:,.0f}円（税抜）")
            click.echo(f"消費税: {total_tax:,.0f}円")
            click.echo(f"合計: {total_amount:,.0f}円（税込）")
            click.echo()

        # JSON出力
        import json
        invoice_data = [invoice.to_dict() for invoice in invoices]

        with open(output, 'w', encoding='utf-8') as f:
            json.dump(invoice_data, f, ensure_ascii=False, indent=2)

        formatters.print_success(f"請求書データを出力しました: {output}")
        formatters.print_success(f"{len(invoices)}件の請求書を作成しました")

    except NotionToMFError as e:
        formatters.print_error(f"エラー: {e}")
        raise click.Abort()

    except Exception as e:
        formatters.print_error(f"予期しないエラー: {e}")
        raise click.Abort()


@cli.command()
def auth():
    """MoneyForwardで認証

    \b
    OAuth 2.0認証フローを開始します。
    ブラウザが自動的に開き、MoneyForwardにログインして認可を行います。

    例:
        python -m src auth
    """
    try:
        formatters.print_info("MoneyForward OAuth 2.0認証を開始します...")
        formatters.print_info("ブラウザが開きます。MoneyForwardにログインして認可してください。")

        auth_client = MoneyForwardAuth()
        token_data = auth_client.authenticate()

        formatters.print_success("認証が完了しました！")
        formatters.print_info("これでMoneyForward APIを使用できます")

        # 接続テスト
        formatters.print_info("接続をテスト中...")
        mf_service = MoneyForwardService()
        if mf_service.test_connection():
            formatters.print_success("MoneyForward APIに正常に接続できました")
        else:
            formatters.print_warning("接続テストに失敗しました")

    except AuthenticationError as e:
        formatters.print_error(f"認証エラー: {e}")
        raise click.Abort()

    except Exception as e:
        formatters.print_error(f"予期しないエラー: {e}")
        raise click.Abort()


@cli.command()
@click.option(
    '--notion-id',
    type=str,
    help='Notion案件ID（指定した案件から請求書を作成）'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='実際には作成せず、プレビューのみ表示'
)
def create_invoice(notion_id: Optional[str], dry_run: bool):
    """対話式で請求書を作成

    \b
    Notionの研修案件からMoneyForwardの請求書を作成します。

    例:
        python -m src create-invoice
        python -m src create-invoice --notion-id 12345
        python -m src create-invoice --dry-run
    """
    try:
        # 設定検証
        config.validate()

        # サービス初期化
        notion = NotionService()
        mf_service = MoneyForwardService()
        mapper = InvoiceMapper()

        # Notion案件を選択
        if notion_id:
            # 指定されたIDの案件を取得（実装簡略化のため、ここではエラー）
            formatters.print_error("--notion-id オプションは未実装です")
            formatters.print_info("現在は対話式選択のみサポートしています")
            raise click.Abort()

        # 最近の完了案件を取得
        formatters.print_info("最近の完了案件を取得中...")
        projects = notion.fetch_training_projects(
            status_filter='完了',
            limit=10
        )

        if not projects:
            formatters.print_warning("完了した案件が見つかりませんでした")
            return

        # 案件を選択
        formatters.print_info(f"\n{len(projects)}件の案件が見つかりました:")
        for i, project in enumerate(projects, 1):
            click.echo(f"{i}. {project.title} - {project.format_amount()}")

        choice = click.prompt('\n作成する案件番号を選択してください', type=int)

        if choice < 1 or choice > len(projects):
            formatters.print_error("無効な選択です")
            raise click.Abort()

        selected_project = projects[choice - 1]

        # 請求書に変換
        formatters.print_info(f"\n請求書を作成中: {selected_project.title}")
        invoice = mapper.map_to_invoice(selected_project)

        # プレビュー表示
        formatters.print_info("\n=== 請求書プレビュー ===")
        click.echo(invoice.format_summary())

        if dry_run:
            formatters.print_info("\n[DRY RUN] 実際には作成しません")
            return

        # 確認
        if not click.confirm('\nこの請求書をMoneyForwardに作成しますか？'):
            formatters.print_info("キャンセルしました")
            return

        # MoneyForwardに作成
        formatters.print_info("MoneyForwardに請求書を作成中...")
        result = mf_service.create_invoice(invoice)

        formatters.print_success("請求書を作成しました！")
        if 'id' in result:
            formatters.print_info(f"請求書ID: {result['id']}")

        # 請求済みフラグを更新
        if invoice.source_id:
            formatters.print_info("Notionの請求済みフラグを更新中...")
            if notion.update_invoiced_status(invoice.source_id):
                formatters.print_success("請求済みフラグを更新しました")
            else:
                formatters.print_warning("請求済みフラグの更新に失敗しました")

    except NotionToMFError as e:
        formatters.print_error(f"エラー: {e}")
        raise click.Abort()

    except Exception as e:
        formatters.print_error(f"予期しないエラー: {e}")
        raise click.Abort()


@cli.command()
@click.option(
    '--status',
    type=click.Choice(['受注', '実施中', '完了'], case_sensitive=False),
    default='完了',
    help='ステータスでフィルタ（デフォルト: 完了）'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='実際には作成せず、プレビューのみ表示'
)
@click.option(
    '--limit',
    type=int,
    help='処理する件数の上限'
)
def sync(status: str, dry_run: bool, limit: Optional[int]):
    """Notionの案件をMoneyForwardに自動同期

    \b
    指定したステータスの案件を取得し、まだ請求書が作成されていないものを
    自動的にMoneyForwardに作成します。

    例:
        python -m src sync
        python -m src sync --status 完了
        python -m src sync --dry-run
        python -m src sync --limit 5
    """
    try:
        # 設定検証
        config.validate()

        # サービス初期化
        notion = NotionService()
        mf_service = MoneyForwardService()
        mapper = InvoiceMapper()

        # データ取得
        formatters.print_info(f"Notionから{status}の案件を取得中...")
        projects = notion.fetch_training_projects(
            status_filter=status,
            limit=limit
        )

        if not projects:
            formatters.print_warning("データが見つかりませんでした")
            return

        formatters.print_info(f"{len(projects)}件の案件を取得しました")

        # 請求書に変換
        formatters.print_info("請求書形式に変換中...")
        invoices, errors = mapper.map_batch(projects, skip_errors=True)

        if errors:
            formatters.print_warning(f"{len(errors)}件のエラーがありました:")
            for error in errors[:5]:  # 最初の5件のみ表示
                formatters.print_error(f"  - {error}")

        if not invoices:
            formatters.print_error("有効な請求書を作成できませんでした")
            raise click.Abort()

        formatters.print_info(f"{len(invoices)}件の請求書を作成します")

        if dry_run:
            formatters.print_info("\n[DRY RUN] 実際には作成しません")
            for i, invoice in enumerate(invoices[:5], 1):
                click.echo(f"\n{i}. {invoice.project_name}")
                click.echo(f"   {invoice.format_summary()}")
            return

        # 確認
        if not click.confirm(f'\n{len(invoices)}件の請求書をMoneyForwardに作成しますか？'):
            formatters.print_info("キャンセルしました")
            return

        # MoneyForwardに一括作成
        formatters.print_info("MoneyForwardに請求書を作成中...")
        created_count = 0
        failed_count = 0
        invoiced_project_ids = []

        for invoice in invoices:
            try:
                mf_service.create_invoice(invoice)
                created_count += 1
                formatters.print_success(f"作成完了: {invoice.project_name}")

                # 請求書作成成功後、元の案件IDを記録
                if invoice.source_ids:
                    # グループ化請求書の場合
                    invoiced_project_ids.extend(invoice.source_ids)
                elif invoice.source_id:
                    # 通常の請求書の場合
                    invoiced_project_ids.append(invoice.source_id)

            except Exception as e:
                failed_count += 1
                formatters.print_error(f"作成失敗: {invoice.project_name} - {e}")

        # 請求済みフラグを更新
        if invoiced_project_ids:
            formatters.print_info("Notionの請求済みフラグを更新中...")
            success, failed = notion.mark_projects_as_invoiced(invoiced_project_ids)
            if success > 0:
                formatters.print_success(f"請求済みフラグを更新: {success}件")
            if failed > 0:
                formatters.print_warning(f"フラグ更新失敗: {failed}件")

        # 結果表示
        formatters.print_info(f"\n=== 同期結果 ===")
        formatters.print_success(f"成功: {created_count}件")
        if failed_count > 0:
            formatters.print_error(f"失敗: {failed_count}件")

    except NotionToMFError as e:
        formatters.print_error(f"エラー: {e}")
        raise click.Abort()

    except Exception as e:
        formatters.print_error(f"予期しないエラー: {e}")
        raise click.Abort()


@cli.command()
def version():
    """バージョン情報を表示"""
    click.echo("notion-to-mf version 0.3.0")
    click.echo("Notion to MoneyForward 請求書転記ツール")


if __name__ == '__main__':
    cli()
