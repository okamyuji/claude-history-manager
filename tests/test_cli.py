"""cli モジュールのテスト - 対話メニューと結合テスト"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from io import StringIO
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from claude_history_manager.cli import (
    bulk_delete_menu,
    history_menu,
    main,
    main_menu,
    plan_menu,
    search_menu,
    session_menu,
)

if TYPE_CHECKING:
    from pathlib import Path


# ─── ヘルパー ─────────────────────────────────────────────────────────────────


def _capture_console() -> tuple[Console, StringIO]:
    buf = StringIO()
    return Console(file=buf, force_terminal=True, width=120), buf


def _make_session(**kwargs: Any) -> dict[str, Any]:
    jst = timezone(timedelta(hours=9))
    defaults: dict[str, Any] = {
        "id": "test-session",
        "file": MagicMock(),
        "project": "-Users-yujiokamoto-devs-project",
        "timestamp": datetime(2026, 2, 1, 10, 0, tzinfo=jst),
        "first_user_msg": "テストメッセージ",
        "assistant_summary": "テスト応答",
        "git_branch": "main",
        "cwd": "/test/project",
        "version": "2.1.0",
        "msg_count": 10,
        "tool_uses": 3,
        "size_kb": 50.0,
    }
    defaults.update(kwargs)
    return defaults


CLI = "claude_history_manager.cli"


# ═══════════════════════════════════════════════════════════════════════════════
# main() エントリポイント
# ═══════════════════════════════════════════════════════════════════════════════


CFG = "claude_history_manager.config"


class TestMain:
    def test_missing_claude_dir(self, tmp_path: Path) -> None:
        with (
            patch(f"{CFG}.CLAUDE_DIR", tmp_path / "nonexistent"),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()
        assert exc_info.value.code == 1

    def test_sessions_subcommand(self, tmp_path: Path) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CFG}.CLAUDE_DIR", tmp_path),
            patch("sys.argv", ["prog", "sessions"]),
            patch(f"{CLI}.get_all_sessions", return_value=[]),
        ):
            try:
                main()
            finally:
                cli_mod.console = orig

    def test_history_subcommand(self, tmp_path: Path) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CFG}.CLAUDE_DIR", tmp_path),
            patch("sys.argv", ["prog", "history"]),
            patch(f"{CLI}.get_history_entries", return_value=[]),
        ):
            try:
                main()
            finally:
                cli_mod.console = orig

    def test_storage_subcommand(self, tmp_path: Path) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CFG}.CLAUDE_DIR", tmp_path),
            patch("sys.argv", ["prog", "storage"]),
            patch(f"{CLI}.get_storage_info", return_value=[]),
        ):
            try:
                main()
            finally:
                cli_mod.console = orig

    def test_search_subcommand(self, tmp_path: Path) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CFG}.CLAUDE_DIR", tmp_path),
            patch("sys.argv", ["prog", "search", "test", "query"]),
            patch(f"{CLI}.get_all_sessions", return_value=[]),
            patch(f"{CLI}.search_sessions", return_value=[]),
        ):
            try:
                main()
            finally:
                cli_mod.console = orig

    def test_unknown_subcommand(self, tmp_path: Path) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CFG}.CLAUDE_DIR", tmp_path),
            patch("sys.argv", ["prog", "unknown"]),
        ):
            try:
                main()
            finally:
                cli_mod.console = orig
        assert "Usage" in buf.getvalue()

    def test_interactive_mode(self, tmp_path: Path) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CFG}.CLAUDE_DIR", tmp_path),
            patch("sys.argv", ["prog"]),
            patch(f"{CLI}.main_menu"),
        ):
            try:
                main()
            finally:
                cli_mod.console = orig


# ═══════════════════════════════════════════════════════════════════════════════
# main_menu
# ═══════════════════════════════════════════════════════════════════════════════


class TestMainMenu:
    def test_quit(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with patch(f"{CLI}.Prompt") as mock_prompt:
            mock_prompt.ask.return_value = "q"
            try:
                main_menu()
            finally:
                cli_mod.console = orig
        assert "終了" in buf.getvalue()

    def test_choice_1_sessions(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, _ = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.session_menu") as mock_session,
        ):
            mock_prompt.ask.side_effect = ["1", "q"]
            try:
                main_menu()
            finally:
                cli_mod.console = orig
        mock_session.assert_called_once()

    def test_choice_2_history(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, _ = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.history_menu") as mock_hist,
        ):
            mock_prompt.ask.side_effect = ["2", "q"]
            try:
                main_menu()
            finally:
                cli_mod.console = orig
        mock_hist.assert_called_once()

    def test_choice_3_plans(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, _ = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.plan_menu") as mock_plan,
        ):
            mock_prompt.ask.side_effect = ["3", "q"]
            try:
                main_menu()
            finally:
                cli_mod.console = orig
        mock_plan.assert_called_once()

    def test_choice_4_search(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, _ = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.search_menu") as mock_search,
        ):
            mock_prompt.ask.side_effect = ["4", "q"]
            try:
                main_menu()
            finally:
                cli_mod.console = orig
        mock_search.assert_called_once()

    def test_choice_5_bulk_delete(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, _ = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.bulk_delete_menu") as mock_bulk,
        ):
            mock_prompt.ask.side_effect = ["5", "q"]
            try:
                main_menu()
            finally:
                cli_mod.console = orig
        mock_bulk.assert_called_once()

    def test_choice_6_storage(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, _ = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.get_storage_info", return_value=[]),
            patch(f"{CLI}.show_storage"),
        ):
            mock_prompt.ask.side_effect = ["6", "q"]
            try:
                main_menu()
            finally:
                cli_mod.console = orig


# ═══════════════════════════════════════════════════════════════════════════════
# session_menu
# ═══════════════════════════════════════════════════════════════════════════════


class TestSessionMenu:
    def test_no_sessions(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with patch(f"{CLI}.get_all_sessions", return_value=[]):
            try:
                session_menu()
            finally:
                cli_mod.console = orig
        assert "見つかりません" in buf.getvalue()

    def test_back_command(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, _ = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.get_all_sessions", return_value=[_make_session()]),
            patch(f"{CLI}.Prompt") as mock_prompt,
        ):
            mock_prompt.ask.return_value = "b"
            try:
                session_menu()
            finally:
                cli_mod.console = orig

    def test_next_page(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, _ = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        sessions = [_make_session(id=f"s-{i}") for i in range(25)]
        with (
            patch(f"{CLI}.get_all_sessions", return_value=sessions),
            patch(f"{CLI}.Prompt") as mock_prompt,
        ):
            mock_prompt.ask.side_effect = ["n", "b"]
            try:
                session_menu()
            finally:
                cli_mod.console = orig

    def test_prev_page(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, _ = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.get_all_sessions", return_value=[_make_session()]),
            patch(f"{CLI}.Prompt") as mock_prompt,
        ):
            mock_prompt.ask.side_effect = ["p", "b"]
            try:
                session_menu()
            finally:
                cli_mod.console = orig

    def test_view_detail(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, _ = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.get_all_sessions", return_value=[_make_session()]),
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.show_session_detail"),
        ):
            mock_prompt.ask.side_effect = ["1", "b"]
            try:
                session_menu()
            finally:
                cli_mod.console = orig

    def test_view_invalid_number(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.get_all_sessions", return_value=[_make_session()]),
            patch(f"{CLI}.Prompt") as mock_prompt,
        ):
            mock_prompt.ask.side_effect = ["99", "b"]
            try:
                session_menu()
            finally:
                cli_mod.console = orig
        assert "無効な番号" in buf.getvalue()

    def test_delete_session_confirmed(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        mock_file = MagicMock()
        with (
            patch(f"{CLI}.get_all_sessions", return_value=[_make_session(file=mock_file)]),
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.Confirm") as mock_confirm,
            patch(f"{CLI}.delete_session", return_value=True),
        ):
            mock_prompt.ask.side_effect = ["d 1", "b"]
            mock_confirm.ask.return_value = True
            try:
                session_menu()
            finally:
                cli_mod.console = orig
        assert "削除しました" in buf.getvalue()

    def test_delete_invalid_command(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.get_all_sessions", return_value=[_make_session()]),
            patch(f"{CLI}.Prompt") as mock_prompt,
        ):
            mock_prompt.ask.side_effect = ["d abc", "b"]
            try:
                session_menu()
            finally:
                cli_mod.console = orig
        assert "無効なコマンド" in buf.getvalue()

    def test_delete_out_of_range(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.get_all_sessions", return_value=[_make_session()]),
            patch(f"{CLI}.Prompt") as mock_prompt,
        ):
            mock_prompt.ask.side_effect = ["d 99", "b"]
            try:
                session_menu()
            finally:
                cli_mod.console = orig
        assert "無効な番号" in buf.getvalue()

    def test_next_page_at_last_stays(self) -> None:
        """最終ページで n を押してもページが変わらない"""
        import claude_history_manager.cli as cli_mod

        c, _ = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.get_all_sessions", return_value=[_make_session()]),
            patch(f"{CLI}.Prompt") as mock_prompt,
        ):
            mock_prompt.ask.side_effect = ["n", "b"]
            try:
                session_menu()
            finally:
                cli_mod.console = orig


# ═══════════════════════════════════════════════════════════════════════════════
# history_menu
# ═══════════════════════════════════════════════════════════════════════════════


class TestHistoryMenu:
    def _make_entries(self, count: int = 3) -> list[dict[str, Any]]:
        return [
            {
                "display": f"コマンド{i}",
                "timestamp": 1738400000000 + i * 100000,
                "project": "/test",
                "_line_num": i,
            }
            for i in range(count)
        ]

    def test_no_entries(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with patch(f"{CLI}.get_history_entries", return_value=[]):
            try:
                history_menu()
            finally:
                cli_mod.console = orig
        assert "見つかりません" in buf.getvalue()

    def test_back_command(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, _ = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.get_history_entries", return_value=self._make_entries()),
            patch(f"{CLI}.Prompt") as mock_prompt,
        ):
            mock_prompt.ask.return_value = "b"
            try:
                history_menu()
            finally:
                cli_mod.console = orig

    def test_next_prev_page(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, _ = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        entries = self._make_entries(50)
        with (
            patch(f"{CLI}.get_history_entries", return_value=entries),
            patch(f"{CLI}.Prompt") as mock_prompt,
        ):
            mock_prompt.ask.side_effect = ["n", "p", "b"]
            try:
                history_menu()
            finally:
                cli_mod.console = orig

    def test_delete_single(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        entries = self._make_entries()
        with (
            patch(f"{CLI}.get_history_entries", side_effect=[entries, []]),
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.Confirm") as mock_confirm,
            patch(f"{CLI}.delete_history_entries", return_value=1),
        ):
            mock_prompt.ask.side_effect = ["d 1", "b"]
            mock_confirm.ask.return_value = True
            try:
                history_menu()
            finally:
                cli_mod.console = orig
        assert "1件削除しました" in buf.getvalue()

    def test_delete_range(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        entries = self._make_entries(10)
        with (
            patch(f"{CLI}.get_history_entries", side_effect=[entries, []]),
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.Confirm") as mock_confirm,
            patch(f"{CLI}.delete_history_entries", return_value=3),
        ):
            mock_prompt.ask.side_effect = ["d 1-3", "b"]
            mock_confirm.ask.return_value = True
            try:
                history_menu()
            finally:
                cli_mod.console = orig
        assert "3件削除しました" in buf.getvalue()

    def test_delete_invalid_command(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.get_history_entries", return_value=self._make_entries()),
            patch(f"{CLI}.Prompt") as mock_prompt,
        ):
            mock_prompt.ask.side_effect = ["d abc", "b"]
            try:
                history_menu()
            finally:
                cli_mod.console = orig
        assert "無効なコマンド" in buf.getvalue()

    def test_delete_many_shows_truncated(self) -> None:
        """6件以上削除時に '... 他 N件' と表示"""
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        entries = self._make_entries(10)
        with (
            patch(f"{CLI}.get_history_entries", side_effect=[entries, []]),
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.Confirm") as mock_confirm,
            patch(f"{CLI}.delete_history_entries", return_value=8),
        ):
            mock_prompt.ask.side_effect = ["d 1-8", "b"]
            mock_confirm.ask.return_value = True
            try:
                history_menu()
            finally:
                cli_mod.console = orig
        assert "他" in buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# plan_menu
# ═══════════════════════════════════════════════════════════════════════════════


class TestPlanMenu:
    def _make_plan(self, name: str = "plan.md") -> dict[str, Any]:
        jst = timezone(timedelta(hours=9))
        mock_file = MagicMock()
        mock_file.read_text.return_value = "# Test Plan\nContent here"
        return {
            "name": name,
            "file": mock_file,
            "size_kb": 1.5,
            "modified": datetime(2026, 2, 1, 10, 0, tzinfo=jst),
        }

    def test_no_plans(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with patch(f"{CLI}.get_plan_files", return_value=[]):
            try:
                plan_menu()
            finally:
                cli_mod.console = orig
        assert "見つかりません" in buf.getvalue()

    def test_back_command(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, _ = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.get_plan_files", return_value=[self._make_plan()]),
            patch(f"{CLI}.Prompt") as mock_prompt,
        ):
            mock_prompt.ask.return_value = "b"
            try:
                plan_menu()
            finally:
                cli_mod.console = orig

    def test_view_plan(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.get_plan_files", return_value=[self._make_plan()]),
            patch(f"{CLI}.Prompt") as mock_prompt,
        ):
            mock_prompt.ask.side_effect = ["1", "b"]
            try:
                plan_menu()
            finally:
                cli_mod.console = orig
        assert "Test Plan" in buf.getvalue()

    def test_delete_plan_confirmed(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.get_plan_files", return_value=[self._make_plan()]),
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.Confirm") as mock_confirm,
            patch(f"{CLI}.delete_plan", return_value=True),
        ):
            mock_prompt.ask.side_effect = ["d 1", "b"]
            mock_confirm.ask.return_value = True
            try:
                plan_menu()
            finally:
                cli_mod.console = orig
        assert "削除しました" in buf.getvalue()

    def test_delete_plan_invalid(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.get_plan_files", return_value=[self._make_plan()]),
            patch(f"{CLI}.Prompt") as mock_prompt,
        ):
            mock_prompt.ask.side_effect = ["d abc", "b"]
            try:
                plan_menu()
            finally:
                cli_mod.console = orig
        assert "無効なコマンド" in buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# search_menu
# ═══════════════════════════════════════════════════════════════════════════════


class TestSearchMenu:
    def test_empty_query(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, _ = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with patch(f"{CLI}.Prompt") as mock_prompt:
            mock_prompt.ask.return_value = ""
            try:
                search_menu()
            finally:
                cli_mod.console = orig

    def test_no_results(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.get_all_sessions", return_value=[]),
            patch(f"{CLI}.search_sessions", return_value=[]),
        ):
            mock_prompt.ask.return_value = "nonexistent"
            try:
                search_menu()
            finally:
                cli_mod.console = orig
        assert "一致するセッションはありません" in buf.getvalue()

    def test_with_results_and_back(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.get_all_sessions", return_value=[_make_session()]),
            patch(f"{CLI}.search_sessions", return_value=[_make_session()]),
        ):
            mock_prompt.ask.side_effect = ["test", "b"]
            try:
                search_menu()
            finally:
                cli_mod.console = orig
        assert "1件ヒット" in buf.getvalue()

    def test_search_view_detail(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, _ = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.get_all_sessions", return_value=[_make_session()]),
            patch(f"{CLI}.search_sessions", return_value=[_make_session()]),
            patch(f"{CLI}.show_session_detail"),
        ):
            mock_prompt.ask.side_effect = ["test", "1", "b"]
            try:
                search_menu()
            finally:
                cli_mod.console = orig

    def test_search_navigate_pages(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, _ = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.get_all_sessions", return_value=[]),
            patch(f"{CLI}.search_sessions", return_value=[_make_session()]),
        ):
            mock_prompt.ask.side_effect = ["test", "n", "p", "b"]
            try:
                search_menu()
            finally:
                cli_mod.console = orig

    def test_search_delete(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.Confirm") as mock_confirm,
            patch(f"{CLI}.get_all_sessions", return_value=[_make_session()]),
            patch(f"{CLI}.search_sessions", return_value=[_make_session()]),
            patch(f"{CLI}.delete_session", return_value=True),
        ):
            mock_prompt.ask.side_effect = ["test", "d 1", "b"]
            mock_confirm.ask.return_value = True
            try:
                search_menu()
            finally:
                cli_mod.console = orig
        assert "削除しました" in buf.getvalue()

    def test_search_delete_invalid(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, _ = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.get_all_sessions", return_value=[]),
            patch(f"{CLI}.search_sessions", return_value=[_make_session()]),
        ):
            mock_prompt.ask.side_effect = ["test", "d abc", "b"]
            try:
                search_menu()
            finally:
                cli_mod.console = orig


# ═══════════════════════════════════════════════════════════════════════════════
# bulk_delete_menu
# ═══════════════════════════════════════════════════════════════════════════════


class TestBulkDeleteMenu:
    def test_back(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, _ = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with patch(f"{CLI}.Prompt") as mock_prompt:
            mock_prompt.ask.return_value = "b"
            try:
                bulk_delete_menu()
            finally:
                cli_mod.console = orig

    def test_date_delete_valid(self) -> None:
        import claude_history_manager.cli as cli_mod

        jst = timezone(timedelta(hours=9))
        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        old_session = _make_session(timestamp=datetime(2024, 1, 1, 10, 0, tzinfo=jst))
        with (
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.Confirm") as mock_confirm,
            patch(f"{CLI}.get_all_sessions", return_value=[old_session]),
            patch(f"{CLI}.delete_session", return_value=True),
        ):
            mock_prompt.ask.side_effect = ["1", "2025-01-01"]
            mock_confirm.ask.return_value = True
            try:
                bulk_delete_menu()
            finally:
                cli_mod.console = orig
        assert "1件削除しました" in buf.getvalue()

    def test_date_delete_invalid_format(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.get_all_sessions", return_value=[]),
        ):
            mock_prompt.ask.side_effect = ["1", "invalid-date"]
            try:
                bulk_delete_menu()
            finally:
                cli_mod.console = orig
        assert "日付形式が無効" in buf.getvalue()

    def test_date_delete_no_targets(self) -> None:
        import claude_history_manager.cli as cli_mod

        jst = timezone(timedelta(hours=9))
        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        new_session = _make_session(timestamp=datetime(2026, 6, 1, 10, 0, tzinfo=jst))
        with (
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.get_all_sessions", return_value=[new_session]),
        ):
            mock_prompt.ask.side_effect = ["1", "2025-01-01"]
            try:
                bulk_delete_menu()
            finally:
                cli_mod.console = orig
        assert "対象セッションはありません" in buf.getvalue()

    def test_project_delete(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        s1 = _make_session(project="proj-a")
        s2 = _make_session(project="proj-b")
        with (
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.Confirm") as mock_confirm,
            patch(f"{CLI}.get_all_sessions", return_value=[s1, s2]),
            patch(f"{CLI}.delete_session", return_value=True),
        ):
            mock_prompt.ask.side_effect = ["2", "1"]
            mock_confirm.ask.return_value = True
            try:
                bulk_delete_menu()
            finally:
                cli_mod.console = orig
        assert "1件削除しました" in buf.getvalue()

    def test_project_delete_invalid_input(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, _ = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.get_all_sessions", return_value=[_make_session()]),
        ):
            mock_prompt.ask.side_effect = ["2", "abc"]
            try:
                bulk_delete_menu()
            finally:
                cli_mod.console = orig

    def test_project_delete_out_of_range(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, _ = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        with (
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.get_all_sessions", return_value=[_make_session()]),
        ):
            mock_prompt.ask.side_effect = ["2", "99"]
            try:
                bulk_delete_menu()
            finally:
                cli_mod.console = orig

    def test_size_delete(self) -> None:
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        small = _make_session(size_kb=2.0)
        big = _make_session(size_kb=100.0)
        with (
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.IntPrompt") as mock_int_prompt,
            patch(f"{CLI}.Confirm") as mock_confirm,
            patch(f"{CLI}.get_all_sessions", return_value=[small, big]),
            patch(f"{CLI}.delete_session", return_value=True),
        ):
            mock_prompt.ask.return_value = "3"
            mock_int_prompt.ask.return_value = 5
            mock_confirm.ask.return_value = True
            try:
                bulk_delete_menu()
            finally:
                cli_mod.console = orig
        assert "1件削除しました" in buf.getvalue()

    def test_many_targets_shows_truncated(self) -> None:
        """11件以上の対象で '... 他 N件' と表示"""
        import claude_history_manager.cli as cli_mod

        c, buf = _capture_console()
        orig = cli_mod.console
        cli_mod.console = c
        sessions = [_make_session(id=f"s-{i}", size_kb=1.0) for i in range(15)]
        with (
            patch(f"{CLI}.Prompt") as mock_prompt,
            patch(f"{CLI}.IntPrompt") as mock_int_prompt,
            patch(f"{CLI}.Confirm") as mock_confirm,
            patch(f"{CLI}.get_all_sessions", return_value=sessions),
            patch(f"{CLI}.delete_session", return_value=True),
        ):
            mock_prompt.ask.return_value = "3"
            mock_int_prompt.ask.return_value = 5
            mock_confirm.ask.return_value = True
            try:
                bulk_delete_menu()
            finally:
                cli_mod.console = orig
        assert "他" in buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# 結合テスト
# ═══════════════════════════════════════════════════════════════════════════════


class TestIntegration:
    """ファイルシステムを使った結合テスト"""

    def test_session_lifecycle(self, tmp_projects_dir: Path) -> None:
        """セッション取得→検索→削除の一連の流れ"""
        from claude_history_manager.storage import (
            delete_session,
            get_all_sessions,
            search_sessions,
        )

        with patch("claude_history_manager.storage.PROJECTS_DIR", tmp_projects_dir):
            sessions = get_all_sessions()
            assert len(sessions) >= 3

            results = search_sessions(sessions, "プロジェクト1")
            assert len(results) >= 1

            target = results[0]
            assert delete_session(target) is True
            assert not target["file"].exists()

            sessions_after = get_all_sessions()
            assert len(sessions_after) < len(sessions)

    def test_history_lifecycle(self, tmp_history_file: Path) -> None:
        """履歴取得→削除→バックアップの一連の流れ"""
        from claude_history_manager.storage import delete_history_entries, get_history_entries

        with patch("claude_history_manager.storage.HISTORY_FILE", tmp_history_file):
            entries = get_history_entries()
            assert len(entries) == 3

            deleted = delete_history_entries(entries, {0})
            assert deleted == 1

            entries_after = get_history_entries()
            assert len(entries_after) == 2
            assert entries_after[0]["display"] == "テストコマンド2"

        backup = tmp_history_file.with_suffix(".jsonl.bak")
        assert backup.exists()

    def test_plan_lifecycle(self, tmp_plans_dir: Path) -> None:
        """プラン取得→削除の一連の流れ"""
        from claude_history_manager.storage import delete_plan, get_plan_files

        with patch("claude_history_manager.storage.PLANS_DIR", tmp_plans_dir):
            plans = get_plan_files()
            assert len(plans) == 2

            assert delete_plan(plans[0]) is True
            plans_after = get_plan_files()
            assert len(plans_after) == 1

    def test_storage_info_with_data(self, tmp_claude_dir: Path) -> None:
        """実データでのストレージ情報取得"""
        from claude_history_manager.storage import get_storage_info

        with (
            patch("claude_history_manager.storage.PROJECTS_DIR", tmp_claude_dir / "projects"),
            patch("claude_history_manager.storage.HISTORY_FILE", tmp_claude_dir / "history.jsonl"),
            patch("claude_history_manager.storage.PLANS_DIR", tmp_claude_dir / "plans"),
            patch("claude_history_manager.config.CLAUDE_DIR", tmp_claude_dir),
        ):
            info = get_storage_info()
            names = [i[0] for i in info]
            assert "セッションログ" in names
            assert "入力履歴" in names
            for _, _, count, size in info:
                assert count >= 0
                assert size >= 0

    def test_search_no_match_returns_empty(self) -> None:
        """検索で一致なしの場合"""
        from claude_history_manager.storage import search_sessions

        sessions = [_make_session(first_user_msg="テスト")]
        assert search_sessions(sessions, "xxxxxxx") == []

    def test_parse_and_display(self, tmp_session_file: Path) -> None:
        """パース結果をUI表示できる"""
        import claude_history_manager.ui as ui_mod
        from claude_history_manager.parser import parse_jsonl_session
        from claude_history_manager.ui import show_session_detail as show_detail

        info = parse_jsonl_session(tmp_session_file)
        c, buf = _capture_console()
        orig = ui_mod.console
        ui_mod.console = c
        try:
            show_detail(info)
        finally:
            ui_mod.console = orig
        output = buf.getvalue()
        assert "セッション詳細" in output
        assert info["id"] in output
