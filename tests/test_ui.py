"""ui モジュールのテスト - 表示関数を含む網羅テスト"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from typing import Any

from rich.console import Console

from claude_history_manager.ui import (
    format_timestamp,
    project_display_name,
    show_history,
    show_plans,
    show_session_detail,
    show_sessions,
    show_storage,
    truncate,
)

# ═══════════════════════════════════════════════════════════════════════════════
# format_timestamp
# ═══════════════════════════════════════════════════════════════════════════════


class TestFormatTimestamp:
    def test_none(self) -> None:
        assert format_timestamp(None) == "不明"

    def test_datetime_utc(self) -> None:
        dt = datetime(2026, 2, 1, 1, 0, 0, tzinfo=UTC)
        result = format_timestamp(dt)
        assert "2026-02-01" in result
        assert "10:00" in result  # UTC+9

    def test_datetime_jst(self) -> None:
        jst = timezone(timedelta(hours=9))
        dt = datetime(2026, 2, 1, 10, 30, 0, tzinfo=jst)
        result = format_timestamp(dt)
        assert result == "2026-02-01 10:30"

    def test_epoch_millis_int(self) -> None:
        result = format_timestamp(1738400000000)
        assert result != "不明"
        assert "2025" in result or "2026" in result

    def test_epoch_millis_float(self) -> None:
        result = format_timestamp(1738400000000.5)
        assert result != "不明"

    def test_invalid_type_string(self) -> None:
        assert format_timestamp("not a date") == "不明"

    def test_invalid_type_list(self) -> None:
        assert format_timestamp([2026, 2, 1]) == "不明"

    def test_invalid_type_dict(self) -> None:
        assert format_timestamp({"year": 2026}) == "不明"

    def test_zero_epoch(self) -> None:
        result = format_timestamp(0)
        assert result != "不明"
        assert "1970" in result


# ═══════════════════════════════════════════════════════════════════════════════
# project_display_name
# ═══════════════════════════════════════════════════════════════════════════════


class TestProjectDisplayName:
    def test_home_only(self) -> None:
        assert project_display_name("-Users-yujiokamoto") == "~ (HOME)"

    def test_empty_string(self) -> None:
        assert project_display_name("") == "~ (HOME)"

    def test_subproject_deep(self) -> None:
        result = project_display_name("-Users-yujiokamoto-devs-swift-MangaViewer")
        assert result == "devs/swift/MangaViewer"

    def test_subproject_shallow(self) -> None:
        result = project_display_name("-Users-yujiokamoto-project")
        assert result == "project"

    def test_non_matching_prefix(self) -> None:
        result = project_display_name("-Users-other-devs")
        assert "other" in result

    def test_hyphen_replaced(self) -> None:
        result = project_display_name("-Users-yujiokamoto-a-b-c")
        assert result == "a/b/c"


# ═══════════════════════════════════════════════════════════════════════════════
# truncate
# ═══════════════════════════════════════════════════════════════════════════════


class TestTruncate:
    def test_none(self) -> None:
        assert truncate(None) == "-"

    def test_empty(self) -> None:
        assert truncate("") == "-"

    def test_short_text(self) -> None:
        assert truncate("hello", 10) == "hello"

    def test_exact_max(self) -> None:
        assert truncate("a" * 80) == "a" * 80

    def test_over_max(self) -> None:
        result = truncate("a" * 100, 50)
        assert len(result) == 53
        assert result.endswith("...")

    def test_newlines_replaced(self) -> None:
        result = truncate("line1\nline2\nline3", 80)
        assert "\n" not in result
        assert result == "line1 line2 line3"

    def test_whitespace_only(self) -> None:
        assert truncate("   ") == ""

    def test_custom_max_len(self) -> None:
        result = truncate("x" * 20, 10)
        assert result == "x" * 10 + "..."

    def test_default_max_len(self) -> None:
        text = "x" * 100
        result = truncate(text)
        assert len(result) == 83  # 80 + "..."


# ═══════════════════════════════════════════════════════════════════════════════
# show_sessions (出力キャプチャテスト)
# ═══════════════════════════════════════════════════════════════════════════════


def _capture_console() -> tuple[Console, StringIO]:
    buf = StringIO()
    return Console(file=buf, force_terminal=False, width=120), buf


class TestShowSessions:
    def _make_session(self, **kwargs: Any) -> dict[str, Any]:
        defaults: dict[str, Any] = {
            "id": "test-session",
            "file": None,
            "project": "-Users-yujiokamoto-devs-project",
            "timestamp": datetime(2026, 2, 1, 10, 0, tzinfo=UTC),
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

    def test_shows_session_count(self) -> None:
        import claude_history_manager.ui as ui_mod

        c, buf = _capture_console()
        orig = ui_mod.console
        ui_mod.console = c
        try:
            show_sessions([self._make_session()], 0, 20)
        finally:
            ui_mod.console = orig
        output = buf.getvalue()
        assert "1件" in output

    def test_pagination_info(self) -> None:
        import claude_history_manager.ui as ui_mod

        c, buf = _capture_console()
        orig = ui_mod.console
        ui_mod.console = c
        try:
            sessions = [self._make_session(id=f"s-{i}") for i in range(25)]
            show_sessions(sessions, 0, 20)
        finally:
            ui_mod.console = orig
        output = buf.getvalue()
        assert "25件" in output
        assert "1/2" in output

    def test_page_2(self) -> None:
        import claude_history_manager.ui as ui_mod

        c, buf = _capture_console()
        orig = ui_mod.console
        ui_mod.console = c
        try:
            sessions = [self._make_session(id=f"s-{i}") for i in range(25)]
            show_sessions(sessions, 1, 20)
        finally:
            ui_mod.console = orig
        output = buf.getvalue()
        assert "2/2" in output

    def test_branch_displayed(self) -> None:
        import claude_history_manager.ui as ui_mod

        c, buf = _capture_console()
        orig = ui_mod.console
        ui_mod.console = c
        try:
            show_sessions([self._make_session(git_branch="feature/test")], 0, 20)
        finally:
            ui_mod.console = orig
        output = buf.getvalue()
        assert "feature/test" in output

    def test_head_branch_hidden(self) -> None:
        import claude_history_manager.ui as ui_mod

        c, buf = _capture_console()
        orig = ui_mod.console
        ui_mod.console = c
        try:
            show_sessions([self._make_session(git_branch="HEAD")], 0, 20)
        finally:
            ui_mod.console = orig
        output = buf.getvalue()
        assert "(HEAD)" not in output

    def test_empty_sessions(self) -> None:
        import claude_history_manager.ui as ui_mod

        c, buf = _capture_console()
        orig = ui_mod.console
        ui_mod.console = c
        try:
            show_sessions([], 0, 20)
        finally:
            ui_mod.console = orig
        output = buf.getvalue()
        assert "0件" in output

    def test_no_user_msg_uses_summary(self) -> None:
        import claude_history_manager.ui as ui_mod

        c, buf = _capture_console()
        orig = ui_mod.console
        ui_mod.console = c
        try:
            show_sessions(
                [self._make_session(first_user_msg=None, assistant_summary="応答テスト")], 0, 20
            )
        finally:
            ui_mod.console = orig
        output = buf.getvalue()
        assert "応答テスト" in output


# ═══════════════════════════════════════════════════════════════════════════════
# show_session_detail
# ═══════════════════════════════════════════════════════════════════════════════


class TestShowSessionDetail:
    def test_shows_all_fields(self, mock_session_data: list[dict[str, Any]]) -> None:
        import claude_history_manager.ui as ui_mod

        c, buf = _capture_console()
        orig = ui_mod.console
        ui_mod.console = c
        try:
            show_session_detail(mock_session_data[0])
        finally:
            ui_mod.console = orig
        output = buf.getvalue()
        assert "session-1" in output
        assert "main" in output
        assert "テストメッセージ1" in output
        assert "応答1" in output
        assert "Session ID" in output
        assert "セッション詳細" in output

    def test_none_fields(self, mock_session_data: list[dict[str, Any]]) -> None:
        import claude_history_manager.ui as ui_mod

        c, buf = _capture_console()
        orig = ui_mod.console
        ui_mod.console = c
        try:
            show_session_detail(mock_session_data[2])
        finally:
            ui_mod.console = orig
        output = buf.getvalue()
        assert "session-3" in output


# ═══════════════════════════════════════════════════════════════════════════════
# show_history
# ═══════════════════════════════════════════════════════════════════════════════


class TestShowHistory:
    def _make_entries(self, count: int = 3) -> list[dict[str, Any]]:
        return [
            {
                "display": f"コマンド{i}",
                "timestamp": 1738400000000 + i * 100000000,
                "project": f"/Users/yujiokamoto/project{i}",
                "_line_num": i,
            }
            for i in range(count)
        ]

    def test_returns_sorted_entries(self) -> None:
        import claude_history_manager.ui as ui_mod

        c, buf = _capture_console()
        orig = ui_mod.console
        ui_mod.console = c
        try:
            entries = self._make_entries()
            result = show_history(entries)
        finally:
            ui_mod.console = orig
        assert result[0]["timestamp"] >= result[-1]["timestamp"]

    def test_displays_table(self) -> None:
        import claude_history_manager.ui as ui_mod

        c, buf = _capture_console()
        orig = ui_mod.console
        ui_mod.console = c
        try:
            show_history(self._make_entries())
        finally:
            ui_mod.console = orig
        output = buf.getvalue()
        assert "入力履歴" in output
        assert "3件" in output

    def test_pagination(self) -> None:
        import claude_history_manager.ui as ui_mod

        c, buf = _capture_console()
        orig = ui_mod.console
        ui_mod.console = c
        try:
            entries = self._make_entries(50)
            show_history(entries, page=1, page_size=30)
        finally:
            ui_mod.console = orig
        output = buf.getvalue()
        assert "2/2" in output

    def test_empty_entries(self) -> None:
        import claude_history_manager.ui as ui_mod

        c, buf = _capture_console()
        orig = ui_mod.console
        ui_mod.console = c
        try:
            result = show_history([])
        finally:
            ui_mod.console = orig
        assert result == []

    def test_project_path_shortened(self) -> None:
        import claude_history_manager.ui as ui_mod

        c, buf = _capture_console()
        orig = ui_mod.console
        ui_mod.console = c
        try:
            entries = [
                {
                    "display": "test",
                    "timestamp": 1738400000000,
                    "project": "/Users/yujiokamoto/devs/project",
                    "_line_num": 0,
                }
            ]
            show_history(entries)
        finally:
            ui_mod.console = orig
        output = buf.getvalue()
        assert "~/devs/project" in output


# ═══════════════════════════════════════════════════════════════════════════════
# show_plans
# ═══════════════════════════════════════════════════════════════════════════════


class TestShowPlans:
    def test_displays_plans(self) -> None:
        import claude_history_manager.ui as ui_mod

        jst = timezone(timedelta(hours=9))
        c, buf = _capture_console()
        orig = ui_mod.console
        ui_mod.console = c
        try:
            plans = [
                {
                    "name": "plan-alpha.md",
                    "file": None,
                    "size_kb": 1.5,
                    "modified": datetime(2026, 2, 1, 10, 0, tzinfo=jst),
                },
                {
                    "name": "plan-beta.md",
                    "file": None,
                    "size_kb": 3.2,
                    "modified": datetime(2026, 1, 15, 14, 30, tzinfo=jst),
                },
            ]
            show_plans(plans)
        finally:
            ui_mod.console = orig
        output = buf.getvalue()
        assert "2件" in output
        assert "plan-alpha.md" in output
        assert "plan-beta.md" in output
        assert "1.5KB" in output

    def test_empty_plans(self) -> None:
        import claude_history_manager.ui as ui_mod

        c, buf = _capture_console()
        orig = ui_mod.console
        ui_mod.console = c
        try:
            show_plans([])
        finally:
            ui_mod.console = orig
        output = buf.getvalue()
        assert "0件" in output


# ═══════════════════════════════════════════════════════════════════════════════
# show_storage
# ═══════════════════════════════════════════════════════════════════════════════


class TestShowStorage:
    def test_displays_categories(self) -> None:
        import claude_history_manager.ui as ui_mod

        c, buf = _capture_console()
        orig = ui_mod.console
        ui_mod.console = c
        try:
            info: list[tuple[str, Any, int, int]] = [
                ("セッションログ", Path("/test/projects"), 100, 1024 * 1024),
                ("入力履歴", Path("/test/history.jsonl"), 50, 5120),
            ]
            show_storage(info)
        finally:
            ui_mod.console = orig
        output = buf.getvalue()
        assert "セッションログ" in output
        assert "入力履歴" in output
        assert "合計" in output
        assert "ストレージ使用状況" in output

    def test_grand_total(self) -> None:
        import claude_history_manager.ui as ui_mod

        c, buf = _capture_console()
        orig = ui_mod.console
        ui_mod.console = c
        try:
            info: list[tuple[str, Any, int, int]] = [
                ("A", Path("/a"), 10, 1024 * 1024),
                ("B", Path("/b"), 20, 1024 * 1024),
            ]
            show_storage(info)
        finally:
            ui_mod.console = orig
        output = buf.getvalue()
        assert "2.0MB" in output

    def test_empty_info(self) -> None:
        import claude_history_manager.ui as ui_mod

        c, buf = _capture_console()
        orig = ui_mod.console
        ui_mod.console = c
        try:
            show_storage([])
        finally:
            ui_mod.console = orig
        output = buf.getvalue()
        assert "0.0MB" in output
