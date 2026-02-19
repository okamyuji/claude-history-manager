"""テストフィクスチャ"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from pathlib import Path


# ─── セッションJSONL生成ヘルパー ──────────────────────────────────────────────


def _write_jsonl(filepath: Path, lines: list[dict[str, Any]]) -> Path:
    with open(filepath, "w", encoding="utf-8") as f:
        for obj in lines:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    return filepath


def make_session_lines(
    *,
    user_msg: str = "テスト用のメッセージです",
    assistant_msg: str = "テスト用のアシスタント応答です。詳細な説明を含みます。",
    branch: str = "main",
    cwd: str = "/Users/test/project",
    version: str = "2.1.0",
    timestamp: str = "2026-02-01T10:00:00Z",
    extra_users: int = 0,
    include_tool_use: bool = False,
    meta_only: bool = False,
    empty_content: bool = False,
) -> list[dict[str, Any]]:
    """テスト用セッションJSONLの行を生成"""
    lines: list[dict[str, Any]] = [
        {
            "type": "progress",
            "timestamp": timestamp,
            "gitBranch": branch,
            "cwd": cwd,
            "version": version,
            "sessionId": "test-session-id",
            "uuid": "uuid-1",
        },
    ]
    if meta_only:
        lines.append(
            {
                "type": "user",
                "timestamp": timestamp,
                "message": {
                    "role": "user",
                    "content": "<local-command-caveat>meta</local-command-caveat>",
                },
                "isMeta": True,
                "uuid": "uuid-meta",
            }
        )
        return lines

    content: str | list[dict[str, str]] = user_msg
    if empty_content:
        content = ""

    lines.append(
        {
            "type": "user",
            "timestamp": timestamp,
            "message": {"role": "user", "content": content},
            "isMeta": False,
            "uuid": "uuid-2",
        }
    )

    lines.append(
        {
            "type": "assistant",
            "timestamp": timestamp,
            "message": {"role": "assistant", "content": assistant_msg},
            "uuid": "uuid-3",
        }
    )

    for i in range(extra_users):
        lines.append(
            {
                "type": "user",
                "timestamp": timestamp,
                "message": {"role": "user", "content": f"追加質問 {i}"},
                "isMeta": False,
                "uuid": f"uuid-extra-{i}",
            }
        )

    if include_tool_use:
        lines.append({"type": "tool_use", "timestamp": timestamp, "uuid": "uuid-tool"})

    return lines


# ─── セッションファイル系フィクスチャ ──────────────────────────────────────────


@pytest.fixture
def tmp_session_file(tmp_path: Path) -> Path:
    """基本的なセッションJSONLファイル"""
    return _write_jsonl(
        tmp_path / "test-session.jsonl",
        make_session_lines(extra_users=1),
    )


@pytest.fixture
def tmp_session_with_tags(tmp_path: Path) -> Path:
    """タグ付きメッセージを含むセッションファイル"""
    lines: list[dict[str, Any]] = [
        {"type": "progress", "timestamp": "2026-02-01T10:00:00Z", "uuid": "uuid-1"},
        {
            "type": "user",
            "timestamp": "2026-02-01T10:01:00Z",
            "message": {
                "role": "user",
                "content": "<system-reminder>system message</system-reminder>",
            },
            "isMeta": False,
            "uuid": "uuid-2",
        },
        {
            "type": "user",
            "timestamp": "2026-02-01T10:01:01Z",
            "message": {
                "role": "user",
                "content": [
                    {"type": "text", "text": "<system-reminder>skip</system-reminder>"},
                    {"type": "text", "text": "実際のユーザー入力"},
                ],
            },
            "isMeta": False,
            "uuid": "uuid-3",
        },
    ]
    return _write_jsonl(tmp_path / "tag-session.jsonl", lines)


@pytest.fixture
def tmp_session_early_exit(tmp_path: Path) -> Path:
    """早期終了条件をトリガーするセッション (msg_count > 5 + user_msg + summary)"""
    return _write_jsonl(
        tmp_path / "early-exit.jsonl",
        make_session_lines(extra_users=10),
    )


@pytest.fixture
def tmp_session_with_tool_use(tmp_path: Path) -> Path:
    """tool_use メッセージを含むセッション"""
    return _write_jsonl(
        tmp_path / "tool-session.jsonl",
        make_session_lines(include_tool_use=True),
    )


@pytest.fixture
def tmp_session_meta_only(tmp_path: Path) -> Path:
    """isMeta=True のユーザーメッセージのみ"""
    return _write_jsonl(
        tmp_path / "meta-session.jsonl",
        make_session_lines(meta_only=True),
    )


@pytest.fixture
def tmp_session_empty_lines(tmp_path: Path) -> Path:
    """空行と不正JSONを含むセッション"""
    filepath = tmp_path / "dirty-session.jsonl"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n")  # 空行
        f.write("not-json\n")  # 不正JSON
        f.write(json.dumps({"type": "progress", "timestamp": "2026-01-01T00:00:00Z"}) + "\n")
        f.write(
            json.dumps({"type": "user", "message": {"content": "有効"}, "isMeta": False}) + "\n"
        )
    return filepath


@pytest.fixture
def tmp_session_claude_mem(tmp_path: Path) -> Path:
    """Claude-Mem observer セッション"""
    return _write_jsonl(
        tmp_path / "mem-session.jsonl",
        make_session_lines(user_msg="You are a Claude-Mem observer tool..."),
    )


@pytest.fixture
def tmp_session_numeric_ts(tmp_path: Path) -> Path:
    """数値タイムスタンプ（エポックミリ秒）"""
    lines: list[dict[str, Any]] = [
        {"type": "progress", "timestamp": 1738400000000, "uuid": "uuid-1"},
        {
            "type": "user",
            "timestamp": 1738400001000,
            "message": {"role": "user", "content": "数値タイムスタンプテスト"},
            "isMeta": False,
            "uuid": "uuid-2",
        },
    ]
    return _write_jsonl(tmp_path / "numeric-ts.jsonl", lines)


@pytest.fixture
def tmp_session_no_user_msg(tmp_path: Path) -> Path:
    """ユーザーメッセージなし、短いアシスタント応答のみ"""
    lines: list[dict[str, Any]] = [
        {"type": "progress", "timestamp": "2026-02-01T10:00:00Z"},
        {
            "type": "assistant",
            "message": {"role": "assistant", "content": "短い"},
            "uuid": "uuid-1",
        },
    ]
    return _write_jsonl(tmp_path / "no-user.jsonl", lines)


# ─── ファイルシステム系フィクスチャ ────────────────────────────────────────────


@pytest.fixture
def tmp_history_file(tmp_path: Path) -> Path:
    """テスト用の history.jsonl"""
    entries = [
        {
            "display": "テストコマンド1",
            "timestamp": 1738400000000,
            "project": "/Users/test/project1",
        },
        {
            "display": "テストコマンド2",
            "timestamp": 1738500000000,
            "project": "/Users/test/project2",
        },
        {"display": "/init", "timestamp": 1738600000000, "project": "/Users/test/project3"},
    ]
    return _write_jsonl(tmp_path / "history.jsonl", entries)


@pytest.fixture
def tmp_projects_dir(tmp_path: Path) -> Path:
    """テスト用のprojectsディレクトリ構造"""
    projects = tmp_path / "projects"

    # プロジェクト1: 通常のセッション
    proj1 = projects / "-Users-test-devs-project1"
    proj1.mkdir(parents=True)
    _write_jsonl(
        proj1 / "session-aaa.jsonl",
        make_session_lines(
            user_msg="プロジェクト1のテスト",
            branch="main",
            timestamp="2026-02-01T10:00:00Z",
        ),
    )

    # プロジェクト1: 2番目のセッション（古い）
    _write_jsonl(
        proj1 / "session-bbb.jsonl",
        make_session_lines(
            user_msg="古いセッション",
            branch="develop",
            timestamp="2025-01-01T10:00:00Z",
        ),
    )

    # プロジェクト2: 別プロジェクト
    proj2 = projects / "-Users-test-devs-project2"
    proj2.mkdir(parents=True)
    _write_jsonl(
        proj2 / "session-ccc.jsonl",
        make_session_lines(
            user_msg="プロジェクト2のテスト",
            branch="feature/test",
            timestamp="2026-02-02T10:00:00Z",
        ),
    )

    # subagentsディレクトリ (スキップされるべき)
    subagents = proj1 / "subagents"
    subagents.mkdir()
    _write_jsonl(
        subagents / "sub-session.jsonl",
        make_session_lines(user_msg="サブエージェントセッション"),
    )

    # 空セッション (msg_count=0, size < 1KB でもない場合)
    empty = projects / "-Users-test-devs-empty"
    empty.mkdir(parents=True)
    tiny = empty / "tiny.jsonl"
    tiny.write_text("{}\n")

    return projects


@pytest.fixture
def tmp_plans_dir(tmp_path: Path) -> Path:
    """テスト用のプランディレクトリ"""
    plans = tmp_path / "plans"
    plans.mkdir()
    (plans / "plan-alpha.md").write_text("# Plan Alpha\nTest plan content", encoding="utf-8")
    (plans / "plan-beta.md").write_text("# Plan Beta\nAnother plan", encoding="utf-8")
    return plans


@pytest.fixture
def tmp_claude_dir(tmp_path: Path, tmp_projects_dir: Path, tmp_plans_dir: Path) -> Path:
    """完全なテスト用 .claude ディレクトリ"""
    claude_dir = tmp_path

    # history.jsonl
    _write_jsonl(
        claude_dir / "history.jsonl",
        [
            {"display": "コマンド1", "timestamp": 1738400000000, "project": "/test"},
            {"display": "コマンド2", "timestamp": 1738500000000, "project": "/test2"},
        ],
    )

    # debug ディレクトリ
    debug = claude_dir / "debug"
    debug.mkdir()
    (debug / "log1.txt").write_text("debug log 1")

    # shell-snapshots
    shells = claude_dir / "shell-snapshots"
    shells.mkdir()
    (shells / "snapshot-1.sh").write_text("#!/bin/bash")

    # file-history
    fh = claude_dir / "file-history"
    fh.mkdir()
    sub = fh / "uuid1"
    sub.mkdir()
    (sub / "file.bak").write_text("backup")

    return claude_dir


@pytest.fixture
def mock_session_data() -> list[dict[str, Any]]:
    """テスト用のセッションデータリスト"""
    jst = timezone(timedelta(hours=9))
    return [
        {
            "id": "session-1",
            "file": None,
            "project": "-Users-test-devs-projectA",
            "timestamp": datetime(2026, 2, 1, 10, 0, tzinfo=jst),
            "first_user_msg": "テストメッセージ1",
            "assistant_summary": "応答1",
            "git_branch": "main",
            "cwd": "/test/projectA",
            "version": "2.1.0",
            "msg_count": 10,
            "tool_uses": 3,
            "size_kb": 50.0,
        },
        {
            "id": "session-2",
            "file": None,
            "project": "-Users-test-devs-projectB",
            "timestamp": datetime(2026, 2, 2, 10, 0, tzinfo=jst),
            "first_user_msg": "Swift MangaViewer のバグ修正",
            "assistant_summary": "修正しました",
            "git_branch": "feature/fix",
            "cwd": "/test/projectB",
            "version": "2.1.0",
            "msg_count": 5,
            "tool_uses": 1,
            "size_kb": 20.0,
        },
        {
            "id": "session-3",
            "file": None,
            "project": "-Users-test",
            "timestamp": None,
            "first_user_msg": None,
            "assistant_summary": None,
            "git_branch": None,
            "cwd": None,
            "version": None,
            "msg_count": 0,
            "tool_uses": 0,
            "size_kb": 1.0,
        },
    ]
