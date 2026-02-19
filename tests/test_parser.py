"""parser モジュールのテスト - 単体テスト + エッジケース"""

from __future__ import annotations

import contextlib
from datetime import datetime
from typing import TYPE_CHECKING

from claude_history_manager.parser import (
    classify_user_message,
    extract_text_from_content,
    parse_jsonl_session,
    parse_timestamp,
)

if TYPE_CHECKING:
    from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════════════
# extract_text_from_content
# ═══════════════════════════════════════════════════════════════════════════════


class TestExtractTextFromContent:
    """contentフィールドからのテキスト抽出"""

    # 正常系
    def test_string_content(self) -> None:
        assert extract_text_from_content("hello world") == "hello world"

    def test_string_with_whitespace(self) -> None:
        assert extract_text_from_content("  hello  ") == "hello"

    def test_list_content_text_items(self) -> None:
        content = [{"type": "text", "text": "first"}, {"type": "text", "text": "second"}]
        assert extract_text_from_content(content) == "first second"

    def test_list_with_string_items(self) -> None:
        assert extract_text_from_content(["hello", "world"]) == "hello world"

    # フィルタリング
    def test_list_content_filters_system_tags(self) -> None:
        content = [
            {"type": "text", "text": "<system-reminder>skip</system-reminder>"},
            {"type": "text", "text": "actual content"},
        ]
        assert extract_text_from_content(content) == "actual content"

    def test_list_filters_all_tags(self) -> None:
        content = [
            {"type": "text", "text": "  <ide_opened_file>skip</ide_opened_file>"},
            {"type": "text", "text": "<command-name>skip</command-name>"},
        ]
        assert extract_text_from_content(content) == ""

    def test_list_filters_string_tags(self) -> None:
        content = ["<tag>skip</tag>", "keep me"]
        assert extract_text_from_content(content) == "keep me"

    # 異常系・境界値
    def test_empty_string(self) -> None:
        assert extract_text_from_content("") == ""

    def test_empty_list(self) -> None:
        assert extract_text_from_content([]) == ""

    def test_none_input(self) -> None:
        assert extract_text_from_content(None) == ""

    def test_integer_input(self) -> None:
        assert extract_text_from_content(42) == ""

    def test_dict_input(self) -> None:
        assert extract_text_from_content({"key": "value"}) == ""

    def test_list_with_non_text_type(self) -> None:
        content = [{"type": "tool_result", "content": "result"}]
        assert extract_text_from_content(content) == ""

    def test_list_item_missing_text_key(self) -> None:
        content = [{"type": "text"}]
        assert extract_text_from_content(content) == ""

    def test_list_with_mixed_types(self) -> None:
        content = [
            {"type": "text", "text": "text item"},
            "string item",
            {"type": "image", "url": "http://example.com"},
            42,  # 非文字列・非dictアイテム
        ]
        assert extract_text_from_content(content) == "text item string item"

    def test_whitespace_only_string(self) -> None:
        assert extract_text_from_content("   ") == ""


# ═══════════════════════════════════════════════════════════════════════════════
# parse_timestamp
# ═══════════════════════════════════════════════════════════════════════════════


class TestParseTimestamp:
    """タイムスタンプの解析"""

    # 正常系
    def test_iso_string_utc(self) -> None:
        result = parse_timestamp("2026-02-01T10:00:00Z")
        assert result is not None
        assert result.year == 2026
        assert result.month == 2
        assert result.day == 1

    def test_iso_string_with_offset(self) -> None:
        result = parse_timestamp("2026-02-01T19:00:00+09:00")
        assert result is not None

    def test_epoch_millis_int(self) -> None:
        result = parse_timestamp(1738400000000)
        assert result is not None
        assert isinstance(result, datetime)

    def test_epoch_millis_float(self) -> None:
        result = parse_timestamp(1738400000000.5)
        assert result is not None

    # 異常系・境界値
    def test_invalid_string(self) -> None:
        assert parse_timestamp("not a date") is None

    def test_none(self) -> None:
        assert parse_timestamp(None) is None

    def test_empty_string(self) -> None:
        assert parse_timestamp("") is None

    def test_boolean(self) -> None:
        # boolはintのサブクラスだが、タイムスタンプとしては無効な値域
        # True=1 は epoch 0.001 秒なのでパース自体は成功する
        result = parse_timestamp(True)
        assert result is not None  # True == 1 なので epoch 付近

    def test_negative_epoch(self) -> None:
        result = parse_timestamp(-1000)
        assert result is not None  # 1970年より前の日付

    def test_extremely_large_epoch(self) -> None:
        # OSError を引き起こす可能性がある超大きい値
        result = parse_timestamp(99999999999999999)
        assert result is None

    def test_list_input(self) -> None:
        assert parse_timestamp([2026, 2, 1]) is None

    def test_dict_input(self) -> None:
        assert parse_timestamp({"year": 2026}) is None


# ═══════════════════════════════════════════════════════════════════════════════
# classify_user_message
# ═══════════════════════════════════════════════════════════════════════════════


class TestClassifyUserMessage:
    """ユーザーメッセージの分類"""

    # 正常系
    def test_normal_message(self) -> None:
        assert classify_user_message("テスト用のメッセージです") == "テスト用のメッセージです"

    def test_long_message_truncated(self) -> None:
        long_msg = "a" * 300
        result = classify_user_message(long_msg)
        assert result is not None
        assert len(result) == 200

    # フィルタリング
    def test_tag_message(self) -> None:
        assert classify_user_message("<system-reminder>skip</system-reminder>") is None

    def test_claude_mem_message(self) -> None:
        result = classify_user_message("You are a Claude-Mem observer tool...")
        assert result == "[claude-mem observer]"

    # 境界値
    def test_short_message_5chars(self) -> None:
        assert classify_user_message("12345") is None  # len <= 5

    def test_short_message_6chars(self) -> None:
        assert classify_user_message("123456") == "123456"  # len > 5

    def test_empty(self) -> None:
        assert classify_user_message("") is None

    def test_exactly_200_chars(self) -> None:
        msg = "x" * 200
        assert classify_user_message(msg) == msg

    def test_201_chars_truncated(self) -> None:
        msg = "x" * 201
        result = classify_user_message(msg)
        assert result is not None
        assert len(result) == 200


# ═══════════════════════════════════════════════════════════════════════════════
# parse_jsonl_session
# ═══════════════════════════════════════════════════════════════════════════════


class TestParseJsonlSession:
    """JSONLセッションファイルの解析"""

    # 正常系
    def test_basic_session(self, tmp_session_file: Path) -> None:
        info = parse_jsonl_session(tmp_session_file)
        assert info["id"] == "test-session"
        assert info["git_branch"] == "main"
        assert info["cwd"] == "/Users/test/project"
        assert info["version"] == "2.1.0"
        assert info["first_user_msg"] == "テスト用のメッセージです"
        assert info["assistant_summary"] is not None
        assert "テスト用のアシスタント応答" in info["assistant_summary"]
        assert info["msg_count"] >= 2

    def test_session_with_tags(self, tmp_session_with_tags: Path) -> None:
        info = parse_jsonl_session(tmp_session_with_tags)
        assert info["first_user_msg"] == "実際のユーザー入力"

    def test_timestamp_parsed(self, tmp_session_file: Path) -> None:
        info = parse_jsonl_session(tmp_session_file)
        assert info["timestamp"] is not None
        assert isinstance(info["timestamp"], datetime)
        assert info["timestamp"].tzinfo is not None

    def test_early_exit_with_many_messages(self, tmp_session_early_exit: Path) -> None:
        info = parse_jsonl_session(tmp_session_early_exit)
        assert info["first_user_msg"] is not None
        assert info["assistant_summary"] is not None
        assert info["msg_count"] > 5

    def test_tool_use_counted(self, tmp_session_with_tool_use: Path) -> None:
        info = parse_jsonl_session(tmp_session_with_tool_use)
        assert info["tool_uses"] >= 1

    def test_meta_only_session(self, tmp_session_meta_only: Path) -> None:
        info = parse_jsonl_session(tmp_session_meta_only)
        assert info["first_user_msg"] is None  # isMeta=True はスキップ

    def test_empty_lines_and_invalid_json(self, tmp_session_empty_lines: Path) -> None:
        info = parse_jsonl_session(tmp_session_empty_lines)
        assert info["timestamp"] is not None
        assert "error" not in info

    def test_claude_mem_session(self, tmp_session_claude_mem: Path) -> None:
        info = parse_jsonl_session(tmp_session_claude_mem)
        assert info["first_user_msg"] == "[claude-mem observer]"

    def test_numeric_timestamp(self, tmp_session_numeric_ts: Path) -> None:
        info = parse_jsonl_session(tmp_session_numeric_ts)
        assert info["timestamp"] is not None
        assert isinstance(info["timestamp"], datetime)

    def test_no_user_msg_short_assistant(self, tmp_session_no_user_msg: Path) -> None:
        """短いアシスタント応答（10文字以下）は summary にならない"""
        info = parse_jsonl_session(tmp_session_no_user_msg)
        assert info["first_user_msg"] is None
        assert info["assistant_summary"] is None  # "短い" は 2文字 < 10

    # 異常系
    def test_nonexistent_file(self, tmp_path: Path) -> None:
        fake = tmp_path / "nonexistent.jsonl"
        with contextlib.suppress(FileNotFoundError):
            parse_jsonl_session(fake)

    def test_size_calculated(self, tmp_session_file: Path) -> None:
        info = parse_jsonl_session(tmp_session_file)
        assert info["size_kb"] > 0

    def test_file_id_from_stem(self, tmp_session_file: Path) -> None:
        info = parse_jsonl_session(tmp_session_file)
        assert info["id"] == tmp_session_file.stem

    def test_project_from_parent(self, tmp_session_file: Path) -> None:
        info = parse_jsonl_session(tmp_session_file)
        assert info["project"] == tmp_session_file.parent.name
