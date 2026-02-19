"""CLI エントリポイントと対話メニュー"""

from __future__ import annotations

import sys
from datetime import datetime
from typing import Any

from rich import box
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt

from .config import JST
from .storage import (
    delete_history_entries,
    delete_plan,
    delete_session,
    get_all_sessions,
    get_history_entries,
    get_plan_files,
    get_storage_info,
    search_sessions,
)
from .ui import (
    console,
    format_timestamp,
    project_display_name,
    show_history,
    show_plans,
    show_session_detail,
    show_sessions,
    show_storage,
    truncate,
)


def session_menu() -> None:
    """セッション管理メニュー"""
    console.print("[dim]セッション情報を読み込み中...[/dim]")
    sessions = get_all_sessions()
    if not sessions:
        console.print("[yellow]セッションが見つかりません[/yellow]")
        return

    page = 0
    page_size = 20

    while True:
        show_sessions(sessions, page, page_size)
        console.print(
            "\n  [cyan]番号[/cyan] 詳細を見る   "
            "[red]d 番号[/red] 削除   "
            "[dim]n[/dim] 次ページ  [dim]p[/dim] 前ページ  [dim]b[/dim] 戻る"
        )
        cmd = Prompt.ask("[dim]番号 or コマンド[/dim]", default="b")

        if cmd == "b":
            break
        elif cmd == "n":
            max_page = (len(sessions) - 1) // page_size
            if page < max_page:
                page += 1
        elif cmd == "p":
            if page > 0:
                page -= 1
        elif cmd.startswith("d "):
            try:
                idx = int(cmd.split()[1]) - 1
                if 0 <= idx < len(sessions):
                    s = sessions[idx]
                    console.print(
                        f"\n削除対象: {project_display_name(s['project'])}"
                        f" / {format_timestamp(s['timestamp'])}"
                    )
                    console.print(f"概要: {truncate(s.get('first_user_msg'), 100)}")
                    if Confirm.ask("本当に削除しますか？") and delete_session(s):
                        sessions.pop(idx)
                        console.print("[green]削除しました[/green]")
                else:
                    console.print("[red]無効な番号です[/red]")
            except (ValueError, IndexError):
                console.print("[red]無効なコマンドです[/red]")
        elif cmd.isdigit():
            idx = int(cmd) - 1
            if 0 <= idx < len(sessions):
                show_session_detail(sessions[idx])
            else:
                console.print("[red]無効な番号です[/red]")


def history_menu() -> None:
    """入力履歴管理メニュー"""
    entries = get_history_entries()
    if not entries:
        console.print("[yellow]入力履歴が見つかりません[/yellow]")
        return

    page = 0
    page_size = 30

    while True:
        sorted_entries = show_history(entries, page, page_size)
        console.print(
            "\n  [red]d 番号[/red] 削除   "
            "[red]d 1-10[/red] 範囲削除   "
            "[red]d 1,3,5[/red] 複数削除\n"
            "  [dim]n[/dim] 次ページ  [dim]p[/dim] 前ページ  [dim]b[/dim] 戻る"
        )
        cmd = Prompt.ask("[dim]コマンド (d/n/p/b)[/dim]", default="b")

        if cmd == "b":
            break
        elif cmd == "n":
            max_page = (len(entries) - 1) // page_size
            if page < max_page:
                page += 1
        elif cmd == "p":
            if page > 0:
                page -= 1
        elif cmd.startswith("d "):
            try:
                range_str = cmd.split(maxsplit=1)[1]
                indices: set[int] = set()
                for part in range_str.split(","):
                    part = part.strip()
                    if "-" in part:
                        start_r, end_r = part.split("-")
                        for i in range(int(start_r) - 1, int(end_r)):
                            indices.add(i)
                    else:
                        indices.add(int(part) - 1)

                valid = {i for i in indices if 0 <= i < len(sorted_entries)}
                if valid:
                    console.print(f"\n{len(valid)}件の履歴を削除します:")
                    for i in sorted(valid)[:5]:
                        console.print(f"  - {truncate(sorted_entries[i].get('display', ''), 60)}")
                    if len(valid) > 5:
                        console.print(f"  ... 他 {len(valid) - 5}件")

                    original_indices: set[int] = set()
                    for i in valid:
                        entry = sorted_entries[i]
                        for j, e in enumerate(entries):
                            if e["_line_num"] == entry["_line_num"]:
                                original_indices.add(j)
                                break

                    if Confirm.ask("本当に削除しますか？"):
                        deleted = delete_history_entries(entries, original_indices)
                        console.print(f"[green]{deleted}件削除しました[/green]")
                        entries = get_history_entries()
            except (ValueError, IndexError):
                console.print("[red]無効なコマンドです[/red]")


def plan_menu() -> None:
    """プランファイル管理メニュー"""
    plans = get_plan_files()
    if not plans:
        console.print("[yellow]プランファイルが見つかりません[/yellow]")
        return

    while True:
        show_plans(plans)
        console.print(
            "\n  [cyan]番号[/cyan] 内容を見る   "
            "[red]d 番号[/red] 削除   "
            "[dim]b[/dim] 戻る"
        )
        cmd = Prompt.ask("[dim]番号 or コマンド[/dim]", default="b")

        if cmd == "b":
            break
        elif cmd.startswith("d "):
            try:
                idx = int(cmd.split()[1]) - 1
                if (
                    0 <= idx < len(plans)
                    and Confirm.ask(f"{plans[idx]['name']} を削除しますか？")
                    and delete_plan(plans[idx])
                ):
                    plans.pop(idx)
                    console.print("[green]削除しました[/green]")
            except (ValueError, IndexError):
                console.print("[red]無効なコマンドです[/red]")
        elif cmd.isdigit():
            idx = int(cmd) - 1
            if 0 <= idx < len(plans):
                content = plans[idx]["file"].read_text(encoding="utf-8")
                console.print(Panel(content[:2000], title=plans[idx]["name"], box=box.ROUNDED))


def search_menu() -> None:
    """セッション検索メニュー"""
    query = Prompt.ask("検索キーワード [dim](メッセージ・プロジェクト名・ブランチ名で検索)[/dim]")
    if not query:
        return

    console.print("[dim]検索中...[/dim]")
    sessions = get_all_sessions()
    results = search_sessions(sessions, query)

    if not results:
        console.print(f"[yellow]「{query}」に一致するセッションはありません[/yellow]")
        return

    console.print(f"[green]{len(results)}件ヒット[/green]")
    page = 0
    while True:
        show_sessions(results, page, 20)
        console.print(
            "\n  [cyan]番号[/cyan] 詳細を見る   "
            "[red]d 番号[/red] 削除   "
            "[dim]n[/dim] 次ページ  [dim]p[/dim] 前ページ  [dim]b[/dim] 戻る"
        )
        cmd = Prompt.ask("[dim]番号 or コマンド[/dim]", default="b")

        if cmd == "b":
            break
        elif cmd == "n":
            page += 1
        elif cmd == "p":
            page = max(0, page - 1)
        elif cmd.startswith("d "):
            try:
                idx = int(cmd.split()[1]) - 1
                if (
                    0 <= idx < len(results)
                    and Confirm.ask("本当に削除しますか？")
                    and delete_session(results[idx])
                ):
                    results.pop(idx)
                    console.print("[green]削除しました[/green]")
            except (ValueError, IndexError):
                pass
        elif cmd.isdigit():
            idx = int(cmd) - 1
            if 0 <= idx < len(results):
                show_session_detail(results[idx])


def bulk_delete_menu() -> None:
    """一括削除メニュー"""
    console.print(
        Panel(
            "[bold]一括削除オプション[/bold]\n\n"
            "  [cyan]1[/cyan] / [cyan]d[/cyan]  日付で削除 (指定日より古いセッション)\n"
            "  [cyan]2[/cyan] / [cyan]p[/cyan]  プロジェクト指定削除\n"
            "  [cyan]3[/cyan] / [cyan]s[/cyan]  小サイズセッション削除 (空/極小)\n"
            "  [cyan]b[/cyan]      戻る",
            box=box.ROUNDED,
        )
    )

    choice = Prompt.ask(
        "選択 [dim](d/p/s/b)[/dim]",
        choices=["1", "2", "3", "d", "p", "s", "b"],
        default="b",
    )
    # ショートカットを番号に正規化
    shortcut_map = {"d": "1", "p": "2", "s": "3"}
    choice = shortcut_map.get(choice, choice)
    if choice == "b":
        return

    sessions = get_all_sessions()
    targets: list[dict[str, Any]] = []

    if choice == "1":
        date_str = Prompt.ask("削除基準日 (YYYY-MM-DD, この日より前を削除)")
        try:
            cutoff = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=JST)
            targets = [s for s in sessions if s["timestamp"] and s["timestamp"] < cutoff]
        except ValueError:
            console.print("[red]日付形式が無効です[/red]")
            return

    elif choice == "2":
        projects = sorted({s["project"] for s in sessions})
        for i, p in enumerate(projects, 1):
            count = sum(1 for s in sessions if s["project"] == p)
            console.print(f"  {i:3d}. {project_display_name(p)} ({count}件)")
        try:
            idx = int(Prompt.ask("削除するプロジェクト番号")) - 1
            if 0 <= idx < len(projects):
                targets = [s for s in sessions if s["project"] == projects[idx]]
            else:
                return
        except ValueError:
            return

    elif choice == "3":
        threshold = IntPrompt.ask("削除対象の最大サイズ (KB)", default=5)
        targets = [s for s in sessions if s["size_kb"] <= threshold]

    if not targets:
        console.print("[yellow]対象セッションはありません[/yellow]")
        return

    console.print(f"\n[bold red]{len(targets)}件のセッションが削除対象です[/bold red]")
    for s in targets[:10]:
        console.print(
            f"  - {format_timestamp(s['timestamp'])} | "
            f"{project_display_name(s['project'])} | "
            f"{truncate(s.get('first_user_msg'), 50)}"
        )
    if len(targets) > 10:
        console.print(f"  ... 他 {len(targets) - 10}件")

    total_kb = sum(s["size_kb"] for s in targets)
    console.print(f"\n合計サイズ: {total_kb:.1f}KB ({total_kb / 1024:.2f}MB)")

    if Confirm.ask("[bold red]本当に削除しますか？ (この操作は取り消せません)[/bold red]"):
        deleted = 0
        for s in targets:
            if delete_session(s):
                deleted += 1
        console.print(f"[green]{deleted}件削除しました[/green]")


def main_menu() -> None:
    """メインメニューループ"""
    while True:
        console.print()
        console.print(
            Panel(
                "[bold]Claude Code 履歴管理ツール[/bold]\n\n"
                "  [cyan]1[/cyan] / [cyan]s[/cyan]  セッション会話ログ一覧\n"
                "  [cyan]2[/cyan] / [cyan]h[/cyan]  入力履歴 (history.jsonl)\n"
                "  [cyan]3[/cyan] / [cyan]p[/cyan]  プランファイル\n"
                "  [cyan]4[/cyan] / [cyan]f[/cyan]  セッション検索\n"
                "  [cyan]5[/cyan] / [cyan]x[/cyan]  一括削除 (古いセッション)\n"
                "  [cyan]6[/cyan] / [cyan]i[/cyan]  ストレージ使用状況\n"
                "  [cyan]q[/cyan]      終了",
                title="メインメニュー",
                box=box.DOUBLE,
            )
        )

        choice = Prompt.ask(
            "選択 [dim](s/h/p/f/x/i/q)[/dim]",
            choices=["1", "2", "3", "4", "5", "6", "s", "h", "p", "f", "x", "i", "q"],
            default="s",
        )

        if choice in ("q",):
            console.print("[dim]終了します[/dim]")
            break
        elif choice in ("1", "s"):
            session_menu()
        elif choice in ("2", "h"):
            history_menu()
        elif choice in ("3", "p"):
            plan_menu()
        elif choice in ("4", "f"):
            search_menu()
        elif choice in ("5", "x"):
            bulk_delete_menu()
        elif choice in ("6", "i"):
            show_storage(get_storage_info())


def main() -> None:
    """エントリポイント"""
    from .config import CLAUDE_DIR

    if not CLAUDE_DIR.exists():
        console.print(f"[red]Error: {CLAUDE_DIR} が見つかりません[/red]")
        sys.exit(1)

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "sessions":
            show_sessions(get_all_sessions(), 0, 20)
        elif cmd == "history":
            show_history(get_history_entries())
        elif cmd == "storage":
            show_storage(get_storage_info())
        elif cmd == "search" and len(sys.argv) > 2:
            query = " ".join(sys.argv[2:])
            show_sessions(search_sessions(get_all_sessions(), query), 0, 20)
        else:
            console.print(f"Usage: {sys.argv[0]} [sessions|history|storage|search <query>]")
        return

    console.print(
        Panel(
            "[bold]Claude Code 履歴管理ツール[/bold]\n"
            "セッション・入力履歴・プランを一覧・検索・削除できます",
            style="blue",
        )
    )
    main_menu()
