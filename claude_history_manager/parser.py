"""JSONL セッションファイルのパーサー"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


def extract_text_from_content(content: Any) -> str:
    """メッセージのcontentフィールドからテキストを抽出する。

    contentは文字列またはリスト形式。タグで始まるシステムメッセージはスキップする。
    """
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        texts: list[str] = []
        for item in content:
            t = ""
            if isinstance(item, dict) and item.get("type") == "text":
                t = item.get("text", "")
            elif isinstance(item, str):
                t = item
            if t and not t.strip().startswith("<"):
                texts.append(t)
        return " ".join(texts).strip()

    return ""


def parse_timestamp(ts: Any) -> datetime | None:
    """タイムスタンプを datetime に変換する"""
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            return None
    if isinstance(ts, (int, float)):
        try:
            return datetime.fromtimestamp(ts / 1000, tz=UTC)
        except (ValueError, OSError):
            return None
    return None


def classify_user_message(content: str) -> str | None:
    """ユーザーメッセージを分類し、表示用テキストを返す。

    タグやシステムメッセージは None を返す。
    """
    if not content or len(content) <= 5:
        return None
    if content.startswith("<"):
        return None
    if content.startswith("You are a Claude-Mem"):
        return "[claude-mem observer]"
    return content[:200]


def parse_jsonl_session(filepath: Path) -> dict[str, Any]:
    """JSONLセッションファイルからメタ情報を抽出する"""
    info: dict[str, Any] = {
        "id": filepath.stem,
        "file": filepath,
        "project": filepath.parent.name,
        "timestamp": None,
        "first_user_msg": None,
        "assistant_summary": None,
        "git_branch": None,
        "cwd": None,
        "version": None,
        "msg_count": 0,
        "tool_uses": 0,
        "size_kb": filepath.stat().st_size / 1024,
    }

    try:
        with open(filepath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # タイムスタンプ取得
                ts = obj.get("timestamp")
                if ts and info["timestamp"] is None:
                    info["timestamp"] = parse_timestamp(ts)

                # メタ情報
                if obj.get("gitBranch") and not info["git_branch"]:
                    info["git_branch"] = obj["gitBranch"]
                if obj.get("cwd") and not info["cwd"]:
                    info["cwd"] = obj["cwd"]
                if obj.get("version") and not info["version"]:
                    info["version"] = obj["version"]

                # メッセージ解析
                msg_type = obj.get("type")
                if msg_type == "user":
                    info["msg_count"] += 1
                    if info["first_user_msg"] is None and not obj.get("isMeta"):
                        content = extract_text_from_content(
                            obj.get("message", {}).get("content", "")
                        )
                        info["first_user_msg"] = classify_user_message(content)

                elif msg_type == "assistant":
                    info["msg_count"] += 1
                    if info["assistant_summary"] is None:
                        content = extract_text_from_content(
                            obj.get("message", {}).get("content", "")
                        )
                        if content and len(content) > 10:
                            info["assistant_summary"] = content[:200]

                elif msg_type == "tool_use":
                    info["tool_uses"] += 1

                # 十分な情報が取れたら早期終了
                if info["first_user_msg"] and info["assistant_summary"] and info["msg_count"] > 5:
                    remaining = sum(1 for _ in f)
                    info["msg_count"] += remaining
                    break

    except Exception as e:  # noqa: BLE001
        info["error"] = str(e)

    return info
