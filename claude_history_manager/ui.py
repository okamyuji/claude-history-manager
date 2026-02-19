"""Rich ベースのターミナルUI"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .config import JST

console = Console()


def format_timestamp(ts: Any) -> str:
    """タイムスタンプを JST 形式で表示"""
    if ts is None:
        return "不明"
    if isinstance(ts, (int, float)):
        ts = datetime.fromtimestamp(ts / 1000, tz=UTC)
    if isinstance(ts, datetime):
        return ts.astimezone(JST).strftime("%Y-%m-%d %H:%M")
    return "不明"


def project_display_name(project_name: str) -> str:
    """プロジェクトディレクトリ名を読みやすい形に変換"""
    name = project_name.replace("-Users-yujiokamoto-", "").replace("-Users-yujiokamoto", "~")
    if name in ("~", ""):
        return "~ (HOME)"
    return name.replace("-", "/")


def truncate(text: str | None, max_len: int = 80) -> str:
    """テキストを指定長に切り詰める"""
    if not text:
        return "-"
    text = text.replace("\n", " ").strip()
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def show_sessions(sessions: list[dict[str, Any]], page: int = 0, page_size: int = 20) -> None:
    """セッション一覧を表示"""
    start = page * page_size
    end = start + page_size
    page_sessions = sessions[start:end]
    total_pages = max(1, (len(sessions) + page_size - 1) // page_size)

    console.print(
        f"\n[bold]セッション一覧[/bold] ({len(sessions)}件)  ページ {page + 1}/{total_pages}\n"
    )

    for i, s in enumerate(page_sessions, start=start + 1):
        summary = s.get("first_user_msg") or s.get("assistant_summary") or "-"
        summary = truncate(summary, 70)
        branch = s.get("git_branch", "") or ""
        branch_str = f" [green]({branch})[/green]" if branch and branch != "HEAD" else ""

        console.print(
            f"  [dim]{i:3d}[/dim]  "
            f"[yellow]{format_timestamp(s['timestamp'])}[/yellow]  "
            f"[cyan]{truncate(project_display_name(s['project']), 25)}[/cyan]"
            f"{branch_str}  "
            f"[dim]{s['msg_count']}msg {s['size_kb']:.0f}KB[/dim]"
        )
        console.print(f"       {summary}")


def show_session_detail(session: dict[str, Any]) -> None:
    """セッション詳細を表示"""
    lines = [
        f"[bold]Session ID:[/bold] {session['id']}",
        f"[bold]プロジェクト:[/bold] {project_display_name(session['project'])}",
        f"[bold]日時:[/bold] {format_timestamp(session['timestamp'])}",
        f"[bold]Branch:[/bold] {session.get('git_branch', '-')}",
        f"[bold]CWD:[/bold] {session.get('cwd', '-')}",
        f"[bold]Version:[/bold] {session.get('version', '-')}",
        f"[bold]メッセージ数:[/bold] {session['msg_count']}",
        f"[bold]サイズ:[/bold] {session['size_kb']:.1f}KB",
        f"[bold]ファイル:[/bold] {session['file']}",
        "",
        "[bold yellow]最初のユーザーメッセージ:[/bold yellow]",
        truncate(session.get("first_user_msg"), 500),
        "",
        "[bold yellow]アシスタント応答概要:[/bold yellow]",
        truncate(session.get("assistant_summary"), 500),
    ]
    console.print(Panel("\n".join(lines), title="セッション詳細", box=box.ROUNDED))


def show_history(
    entries: list[dict[str, Any]], page: int = 0, page_size: int = 30
) -> list[dict[str, Any]]:
    """入力履歴テーブルを表示。ソート済みリストを返す。"""
    sorted_entries = sorted(entries, key=lambda e: e.get("timestamp", 0), reverse=True)
    start = page * page_size
    end = start + page_size
    page_entries = sorted_entries[start:end]
    total_pages = max(1, (len(sorted_entries) + page_size - 1) // page_size)

    table = Table(
        title=f"入力履歴 ({len(entries)}件)  ページ {page + 1}/{total_pages}",
        box=box.ROUNDED,
        show_lines=False,
        expand=True,
    )
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("日時", width=16)
    table.add_column("プロジェクト", width=28, style="cyan")
    table.add_column("入力内容", ratio=1)

    for i, e in enumerate(page_entries, start=start + 1):
        project = e.get("project", "")
        project = project.replace("/Users/yujiokamoto/", "~/").replace("/Users/yujiokamoto", "~")
        table.add_row(
            str(i),
            format_timestamp(e.get("timestamp")),
            project,
            truncate(e.get("display", ""), 80),
        )

    console.print(table)
    return sorted_entries


def show_plans(plans: list[dict[str, Any]]) -> None:
    """プランファイルテーブルを表示"""
    table = Table(title=f"プランファイル ({len(plans)}件)", box=box.ROUNDED)
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("ファイル名", style="cyan")
    table.add_column("更新日時", width=16)
    table.add_column("サイズ", width=10, justify="right")

    for i, p in enumerate(plans, 1):
        table.add_row(
            str(i),
            p["name"],
            p["modified"].strftime("%Y-%m-%d %H:%M"),
            f"{p['size_kb']:.1f}KB",
        )
    console.print(table)


def show_storage(info: list[tuple[str, Any, int, int]]) -> None:
    """ストレージ使用状況を表示"""
    table = Table(title="ストレージ使用状況", box=box.ROUNDED)
    table.add_column("カテゴリ", style="cyan")
    table.add_column("パス", style="dim")
    table.add_column("件数", justify="right")
    table.add_column("サイズ", justify="right", style="yellow")

    grand_total = 0
    for name, path, count, size in info:
        grand_total += size
        table.add_row(name, str(path), str(count), f"{size / 1024 / 1024:.1f}MB")

    table.add_row("", "", "[bold]合計[/bold]", f"[bold]{grand_total / 1024 / 1024:.1f}MB[/bold]")
    console.print(table)
