"""設定と定数"""

from datetime import timedelta, timezone
from pathlib import Path

JST = timezone(timedelta(hours=9))
CLAUDE_DIR = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"
HISTORY_FILE = CLAUDE_DIR / "history.jsonl"
PLANS_DIR = CLAUDE_DIR / "plans"
