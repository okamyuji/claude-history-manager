"""storage モジュールのテスト - ファイルI/O操作"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

from claude_history_manager.storage import (
    delete_history_entries,
    delete_plan,
    delete_session,
    get_all_sessions,
    get_history_entries,
    get_plan_files,
    get_storage_info,
    search_sessions,
)

if TYPE_CHECKING:
    from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════════════
# search_sessions (純粋関数、ファイルI/O不要)
# ═══════════════════════════════════════════════════════════════════════════════


class TestSearchSessions:
    def _s(self, **kwargs: Any) -> dict[str, Any]:
        defaults: dict[str, Any] = {
            "first_user_msg": None,
            "assistant_summary": None,
            "project": "test-project",
            "git_branch": None,
            "cwd": None,
        }
        defaults.update(kwargs)
        return defaults

    def test_search_by_user_msg(self) -> None:
        sessions = [self._s(first_user_msg="MangaViewer の修正"), self._s(first_user_msg="別")]
        assert len(search_sessions(sessions, "MangaViewer")) == 1

    def test_search_by_project(self) -> None:
        sessions = [self._s(project="devs-swift-MangaViewer"), self._s(project="devs-python")]
        assert len(search_sessions(sessions, "MangaViewer")) == 1

    def test_search_by_branch(self) -> None:
        sessions = [self._s(git_branch="feature/new"), self._s(git_branch="main")]
        assert len(search_sessions(sessions, "feature")) == 1

    def test_search_by_cwd(self) -> None:
        sessions = [self._s(cwd="/home/user/swift-project"), self._s(cwd="/other")]
        assert len(search_sessions(sessions, "swift")) == 1

    def test_search_by_assistant_summary(self) -> None:
        sessions = [self._s(assistant_summary="修正完了しました")]
        assert len(search_sessions(sessions, "修正完了")) == 1

    def test_search_case_insensitive(self) -> None:
        sessions = [self._s(first_user_msg="Hello World")]
        assert len(search_sessions(sessions, "hello")) == 1

    def test_search_no_results(self) -> None:
        assert len(search_sessions([self._s(first_user_msg="test")], "nonexistent")) == 0

    def test_search_empty_sessions(self) -> None:
        assert len(search_sessions([], "query")) == 0

    def test_search_empty_query(self) -> None:
        sessions = [self._s(first_user_msg="test")]
        assert len(search_sessions(sessions, "")) == 1  # "" は全てにマッチ

    def test_search_none_fields(self) -> None:
        """None フィールドがあってもクラッシュしない"""
        sessions = [self._s()]  # 全てNone
        assert len(search_sessions(sessions, "anything")) == 0

    def test_search_multiple_matches(self) -> None:
        sessions = [self._s(first_user_msg="test A"), self._s(first_user_msg="test B")]
        assert len(search_sessions(sessions, "test")) == 2


# ═══════════════════════════════════════════════════════════════════════════════
# get_all_sessions (ファイルシステム依存)
# ═══════════════════════════════════════════════════════════════════════════════


class TestGetAllSessions:
    def test_with_projects(self, tmp_projects_dir: Path) -> None:
        with patch("claude_history_manager.storage.PROJECTS_DIR", tmp_projects_dir):
            sessions = get_all_sessions()
        # subagentsはスキップ、tinyは空なのでスキップ
        assert len(sessions) >= 3

    def test_sorted_by_timestamp_desc(self, tmp_projects_dir: Path) -> None:
        with patch("claude_history_manager.storage.PROJECTS_DIR", tmp_projects_dir):
            sessions = get_all_sessions()
        timestamps = [s["timestamp"] for s in sessions if s["timestamp"]]
        for i in range(len(timestamps) - 1):
            assert timestamps[i] >= timestamps[i + 1]

    def test_subagents_excluded(self, tmp_projects_dir: Path) -> None:
        with patch("claude_history_manager.storage.PROJECTS_DIR", tmp_projects_dir):
            sessions = get_all_sessions()
        for s in sessions:
            assert "subagent" not in str(s["file"]).lower()

    def test_nonexistent_dir(self, tmp_path: Path) -> None:
        with patch("claude_history_manager.storage.PROJECTS_DIR", tmp_path / "nope"):
            assert get_all_sessions() == []

    def test_empty_dir(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty_projects"
        empty.mkdir()
        with patch("claude_history_manager.storage.PROJECTS_DIR", empty):
            assert get_all_sessions() == []


# ═══════════════════════════════════════════════════════════════════════════════
# get_history_entries
# ═══════════════════════════════════════════════════════════════════════════════


class TestGetHistoryEntries:
    def test_reads_entries(self, tmp_history_file: Path) -> None:
        with patch("claude_history_manager.storage.HISTORY_FILE", tmp_history_file):
            entries = get_history_entries()
        assert len(entries) == 3
        assert entries[0]["display"] == "テストコマンド1"

    def test_line_numbers_set(self, tmp_history_file: Path) -> None:
        with patch("claude_history_manager.storage.HISTORY_FILE", tmp_history_file):
            entries = get_history_entries()
        assert entries[0]["_line_num"] == 0
        assert entries[1]["_line_num"] == 1
        assert entries[2]["_line_num"] == 2

    def test_nonexistent_file(self, tmp_path: Path) -> None:
        with patch("claude_history_manager.storage.HISTORY_FILE", tmp_path / "nope"):
            assert get_history_entries() == []

    def test_empty_file(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty.jsonl"
        empty.write_text("")
        with patch("claude_history_manager.storage.HISTORY_FILE", empty):
            assert get_history_entries() == []

    def test_file_with_empty_lines_and_bad_json(self, tmp_path: Path) -> None:
        filepath = tmp_path / "mixed.jsonl"
        filepath.write_text(
            '\n{"display":"ok","timestamp":1}\nnot-json\n{"display":"ok2","timestamp":2}\n'
        )
        with patch("claude_history_manager.storage.HISTORY_FILE", filepath):
            entries = get_history_entries()
        assert len(entries) == 2


# ═══════════════════════════════════════════════════════════════════════════════
# get_plan_files
# ═══════════════════════════════════════════════════════════════════════════════


class TestGetPlanFiles:
    def test_reads_plans(self, tmp_plans_dir: Path) -> None:
        with patch("claude_history_manager.storage.PLANS_DIR", tmp_plans_dir):
            plans = get_plan_files()
        assert len(plans) == 2
        names = {p["name"] for p in plans}
        assert "plan-alpha.md" in names
        assert "plan-beta.md" in names

    def test_plans_sorted_by_modified_desc(self, tmp_plans_dir: Path) -> None:
        # plan-betaのmtimeを新しくする
        import time

        time.sleep(0.01)
        (tmp_plans_dir / "plan-beta.md").write_text("updated")
        with patch("claude_history_manager.storage.PLANS_DIR", tmp_plans_dir):
            plans = get_plan_files()
        assert plans[0]["name"] == "plan-beta.md"

    def test_nonexistent_dir(self, tmp_path: Path) -> None:
        with patch("claude_history_manager.storage.PLANS_DIR", tmp_path / "nope"):
            assert get_plan_files() == []

    def test_empty_dir(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty_plans"
        empty.mkdir()
        with patch("claude_history_manager.storage.PLANS_DIR", empty):
            assert get_plan_files() == []

    def test_plan_has_expected_fields(self, tmp_plans_dir: Path) -> None:
        with patch("claude_history_manager.storage.PLANS_DIR", tmp_plans_dir):
            plans = get_plan_files()
        for p in plans:
            assert "name" in p
            assert "file" in p
            assert "size_kb" in p
            assert "modified" in p
            assert p["size_kb"] > 0


# ═══════════════════════════════════════════════════════════════════════════════
# delete_session
# ═══════════════════════════════════════════════════════════════════════════════


class TestDeleteSession:
    def test_delete_existing(self, tmp_session_file: Path) -> None:
        assert tmp_session_file.exists()
        result = delete_session({"file": tmp_session_file})
        assert result is True
        assert not tmp_session_file.exists()

    def test_delete_nonexistent(self, tmp_path: Path) -> None:
        fake = tmp_path / "gone.jsonl"
        result = delete_session({"file": fake})
        assert result is False


# ═══════════════════════════════════════════════════════════════════════════════
# delete_history_entries
# ═══════════════════════════════════════════════════════════════════════════════


class TestDeleteHistoryEntries:
    def test_delete_single_entry(self, tmp_history_file: Path) -> None:
        with patch("claude_history_manager.storage.HISTORY_FILE", tmp_history_file):
            entries = get_history_entries()
            deleted = delete_history_entries(entries, {0})
        assert deleted == 1
        # 残り2件
        with open(tmp_history_file) as f:
            remaining = [json.loads(line) for line in f if line.strip()]
        assert len(remaining) == 2
        assert remaining[0]["display"] == "テストコマンド2"

    def test_delete_multiple_entries(self, tmp_history_file: Path) -> None:
        with patch("claude_history_manager.storage.HISTORY_FILE", tmp_history_file):
            entries = get_history_entries()
            deleted = delete_history_entries(entries, {0, 2})
        assert deleted == 2

    def test_delete_all_entries(self, tmp_history_file: Path) -> None:
        with patch("claude_history_manager.storage.HISTORY_FILE", tmp_history_file):
            entries = get_history_entries()
            deleted = delete_history_entries(entries, {0, 1, 2})
        assert deleted == 3

    def test_delete_out_of_range_index(self, tmp_history_file: Path) -> None:
        with patch("claude_history_manager.storage.HISTORY_FILE", tmp_history_file):
            entries = get_history_entries()
            deleted = delete_history_entries(entries, {999})  # 範囲外
        assert deleted == 0

    def test_backup_created(self, tmp_history_file: Path) -> None:
        with patch("claude_history_manager.storage.HISTORY_FILE", tmp_history_file):
            entries = get_history_entries()
            delete_history_entries(entries, {0})
        backup = tmp_history_file.with_suffix(".jsonl.bak")
        assert backup.exists()


# ═══════════════════════════════════════════════════════════════════════════════
# delete_plan
# ═══════════════════════════════════════════════════════════════════════════════


class TestDeletePlan:
    def test_delete_existing(self, tmp_plans_dir: Path) -> None:
        filepath = tmp_plans_dir / "plan-alpha.md"
        assert filepath.exists()
        result = delete_plan({"file": filepath})
        assert result is True
        assert not filepath.exists()

    def test_delete_nonexistent(self, tmp_path: Path) -> None:
        result = delete_plan({"file": tmp_path / "nope.md"})
        assert result is False


# ═══════════════════════════════════════════════════════════════════════════════
# get_storage_info
# ═══════════════════════════════════════════════════════════════════════════════


class TestGetStorageInfo:
    def test_returns_info(self, tmp_claude_dir: Path) -> None:
        with (
            patch("claude_history_manager.storage.PROJECTS_DIR", tmp_claude_dir / "projects"),
            patch("claude_history_manager.storage.HISTORY_FILE", tmp_claude_dir / "history.jsonl"),
            patch("claude_history_manager.storage.PLANS_DIR", tmp_claude_dir / "plans"),
            patch("claude_history_manager.config.CLAUDE_DIR", tmp_claude_dir),
        ):
            info = get_storage_info()
        # セッションログ、入力履歴、プランファイル、デバッグログ、シェルスナップショット、ファイル履歴
        names = [i[0] for i in info]
        assert "セッションログ" in names
        assert "入力履歴" in names
        assert "プランファイル" in names
        assert "デバッグログ" in names
        assert "シェルスナップショット" in names
        assert "ファイル履歴" in names

    def test_all_missing(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty_claude"
        with (
            patch("claude_history_manager.storage.PROJECTS_DIR", empty / "projects"),
            patch("claude_history_manager.storage.HISTORY_FILE", empty / "history.jsonl"),
            patch("claude_history_manager.storage.PLANS_DIR", empty / "plans"),
            patch("claude_history_manager.config.CLAUDE_DIR", empty),
        ):
            info = get_storage_info()
        assert info == []
