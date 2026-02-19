"""データの読み込み・削除操作"""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from .config import HISTORY_FILE, JST, PLANS_DIR, PROJECTS_DIR
from .parser import parse_jsonl_session

if TYPE_CHECKING:
    from pathlib import Path


def get_all_sessions() -> list[dict[str, Any]]:
    """全セッション一覧を取得する"""
    sessions: list[dict[str, Any]] = []
    if not PROJECTS_DIR.exists():
        return sessions

    for jsonl_file in PROJECTS_DIR.rglob("*.jsonl"):
        if "subagents" in str(jsonl_file):
            continue
        info = parse_jsonl_session(jsonl_file)
        if info["msg_count"] > 0 or info["size_kb"] > 1:
            sessions.append(info)

    sessions.sort(
        key=lambda s: s["timestamp"] or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    return sessions


def get_history_entries() -> list[dict[str, Any]]:
    """history.jsonlのエントリ一覧"""
    entries: list[dict[str, Any]] = []
    if not HISTORY_FILE.exists():
        return entries
    with open(HISTORY_FILE, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                obj["_line_num"] = i
                entries.append(obj)
            except json.JSONDecodeError:
                continue
    return entries


def get_plan_files() -> list[dict[str, Any]]:
    """プランファイル一覧"""
    plans: list[dict[str, Any]] = []
    if not PLANS_DIR.exists():
        return plans
    for f in PLANS_DIR.glob("*.md"):
        stat = f.stat()
        plans.append(
            {
                "name": f.name,
                "file": f,
                "size_kb": stat.st_size / 1024,
                "modified": datetime.fromtimestamp(stat.st_mtime, tz=JST),
            }
        )
    plans.sort(key=lambda p: p["modified"], reverse=True)
    return plans


def delete_session(session: dict[str, Any]) -> bool:
    """セッションファイルを削除"""
    filepath: Path = session["file"]
    if filepath.exists():
        filepath.unlink()
        return True
    return False


def delete_history_entries(entries: list[dict[str, Any]], indices_to_delete: set[int]) -> int:
    """history.jsonlから指定行を削除。削除した行数を返す。"""
    line_nums = {entries[i]["_line_num"] for i in indices_to_delete if i < len(entries)}
    with open(HISTORY_FILE, encoding="utf-8") as f:
        all_lines = f.readlines()

    new_lines = [line for i, line in enumerate(all_lines) if i not in line_nums]

    backup = HISTORY_FILE.with_suffix(".jsonl.bak")
    shutil.copy2(HISTORY_FILE, backup)

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return len(all_lines) - len(new_lines)


def delete_plan(plan: dict[str, Any]) -> bool:
    """プランファイルを削除"""
    filepath: Path = plan["file"]
    if filepath.exists():
        filepath.unlink()
        return True
    return False


def search_sessions(sessions: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    """セッションをキーワード検索"""
    query_lower = query.lower()
    results: list[dict[str, Any]] = []
    for s in sessions:
        searchable = " ".join(
            [
                s.get("first_user_msg", "") or "",
                s.get("assistant_summary", "") or "",
                s.get("project", ""),
                s.get("git_branch", "") or "",
                s.get("cwd", "") or "",
            ]
        ).lower()
        if query_lower in searchable:
            results.append(s)
    return results


def get_storage_info() -> list[tuple[str, Path, int, int]]:
    """ストレージ使用状況を取得"""
    from .config import CLAUDE_DIR

    info: list[tuple[str, Path, int, int]] = []

    if PROJECTS_DIR.exists():
        total = sum(f.stat().st_size for f in PROJECTS_DIR.rglob("*.jsonl"))
        count = sum(1 for _ in PROJECTS_DIR.rglob("*.jsonl"))
        info.append(("セッションログ", PROJECTS_DIR, count, total))

    if HISTORY_FILE.exists():
        size = HISTORY_FILE.stat().st_size
        with open(HISTORY_FILE) as f:
            count = sum(1 for _ in f)
        info.append(("入力履歴", HISTORY_FILE, count, size))

    if PLANS_DIR.exists():
        files = list(PLANS_DIR.glob("*.md"))
        total = sum(f.stat().st_size for f in files)
        info.append(("プランファイル", PLANS_DIR, len(files), total))

    for name, dirname in [
        ("デバッグログ", "debug"),
        ("シェルスナップショット", "shell-snapshots"),
        ("ファイル履歴", "file-history"),
    ]:
        d = CLAUDE_DIR / dirname
        if d.exists():
            files = [f for f in d.rglob("*") if f.is_file()]
            total = sum(f.stat().st_size for f in files)
            info.append((name, d, len(files), total))

    return info
