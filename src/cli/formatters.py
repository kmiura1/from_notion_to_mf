"""CLI出力フォーマッター"""
import json
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich import box
from ..models.training_project import TrainingProject

console = Console()


def format_table(projects: List[TrainingProject]) -> None:
    """テーブル形式で表示

    Args:
        projects: 研修案件リスト
    """
    if not projects:
        console.print("[yellow]データが見つかりませんでした[/yellow]")
        return

    table = Table(
        title=f"研修案件一覧 ({len(projects)}件)",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )

    # カラム定義
    table.add_column("案件名", style="white", no_wrap=False, width=30)
    table.add_column("ステータス", style="green", justify="center", width=10)
    table.add_column("顧客名", style="yellow", width=15)
    table.add_column("金額", style="magenta", justify="right", width=12)
    table.add_column("期間", style="cyan", width=20)

    # データ追加
    for project in projects:
        # ステータスに応じて色を変える
        status_color = _get_status_color(project.status)
        status_text = f"[{status_color}]{project.status or '-'}[/{status_color}]"

        table.add_row(
            project.title,
            status_text,
            project.customer_name or "-",
            project.format_amount(),
            project.format_date_range()
        )

    console.print(table)


def format_detailed(projects: List[TrainingProject]) -> None:
    """詳細形式で表示

    Args:
        projects: 研修案件リスト
    """
    if not projects:
        console.print("[yellow]データが見つかりませんでした[/yellow]")
        return

    console.print(f"\n[bold cyan]研修案件一覧 ({len(projects)}件)[/bold cyan]\n")

    for i, project in enumerate(projects, 1):
        console.print(f"[bold white]━━━ {i}. {project.title} ━━━[/bold white]")
        console.print(f"  [cyan]ステータス:[/cyan] {project.status or '-'}")
        console.print(f"  [cyan]顧客名:[/cyan] {project.customer_name or '-'}")
        console.print(f"  [cyan]金額:[/cyan] {project.format_amount()} (税抜)")
        console.print(f"  [cyan]期間:[/cyan] {project.format_date_range()}")

        if project.location:
            console.print(f"  [cyan]場所:[/cyan] {project.location}")

        if project.format:
            console.print(f"  [cyan]形式:[/cyan] {project.format}")

        if project.participants:
            console.print(f"  [cyan]参加人数:[/cyan] {project.participants}名")

        if project.days:
            console.print(f"  [cyan]日数:[/cyan] {project.days}日")

        if project.notes:
            console.print(f"  [cyan]備考:[/cyan] {project.notes}")

        console.print()


def format_json(projects: List[TrainingProject], pretty: bool = True) -> str:
    """JSON形式で出力

    Args:
        projects: 研修案件リスト
        pretty: 整形するかどうか

    Returns:
        JSON文字列
    """
    data = [project.to_dict() for project in projects]

    if pretty:
        return json.dumps(data, ensure_ascii=False, indent=2)
    else:
        return json.dumps(data, ensure_ascii=False)


def format_csv(projects: List[TrainingProject]) -> str:
    """CSV形式で出力

    Args:
        projects: 研修案件リスト

    Returns:
        CSV文字列
    """
    if not projects:
        return ""

    # ヘッダー
    headers = [
        "案件名", "ステータス", "顧客名", "金額",
        "開始日", "終了日", "場所", "形式",
        "参加人数", "日数", "備考"
    ]

    lines = [",".join(headers)]

    # データ行
    for project in projects:
        row = [
            _escape_csv(project.title),
            _escape_csv(project.status or ""),
            _escape_csv(project.customer_name or ""),
            str(project.amount or 0),
            project.start_date.strftime("%Y-%m-%d") if project.start_date else "",
            project.end_date.strftime("%Y-%m-%d") if project.end_date else "",
            _escape_csv(project.location or ""),
            _escape_csv(project.format or ""),
            str(project.participants or ""),
            str(project.days or ""),
            _escape_csv(project.notes or ""),
        ]
        lines.append(",".join(row))

    return "\n".join(lines)


def print_success(message: str) -> None:
    """成功メッセージを表示

    Args:
        message: メッセージ
    """
    console.print(f"[green][OK][/green] {message}")


def print_error(message: str) -> None:
    """エラーメッセージを表示

    Args:
        message: メッセージ
    """
    console.print(f"[red][ERROR][/red] {message}", style="bold red")


def print_warning(message: str) -> None:
    """警告メッセージを表示

    Args:
        message: メッセージ
    """
    console.print(f"[yellow][WARNING][/yellow] {message}", style="yellow")


def print_info(message: str) -> None:
    """情報メッセージを表示

    Args:
        message: メッセージ
    """
    console.print(f"[blue][INFO][/blue] {message}", style="blue")


def _get_status_color(status: Optional[str]) -> str:
    """ステータスに応じた色を取得

    Args:
        status: ステータス

    Returns:
        色名
    """
    if not status:
        return "white"

    status_colors = {
        "受注": "yellow",
        "実施中": "blue",
        "完了": "green",
    }

    return status_colors.get(status, "white")


def _escape_csv(value: str) -> str:
    """CSV用にエスケープ

    Args:
        value: 値

    Returns:
        エスケープ済み文字列
    """
    if "," in value or '"' in value or "\n" in value:
        escaped = value.replace('"', '""')
        return f'"{escaped}"'
    return value
