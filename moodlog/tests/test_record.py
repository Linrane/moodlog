"""
test_record.py
record 命令的集成测试（使用 Click 的 CliRunner 模拟 CLI 调用）。
通过 monkeypatch 覆盖 config.db_path，让每个测试用独立的临时数据库。
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import patch, PropertyMock

import pytest
from click.testing import CliRunner

from moodlog.main import cli
from moodlog.database import get_mood_by_date, init_db


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_db(tmp_path) -> Path:
    db = tmp_path / "test.db"
    init_db(db)
    return db


def invoke(runner, args, db_path, input_text=None):
    """封装 CLI 调用，通过 mock 注入临时数据库路径。"""
    with patch("moodlog.config.Config.db_path", new_callable=PropertyMock, return_value=db_path):
        return runner.invoke(cli, args, input=input_text, catch_exceptions=False)


# ── 基本记录 ──────────────────────────────────────────────────────

def test_record_with_score(runner, tmp_db):
    result = invoke(runner, ["record", "4"], tmp_db, input_text="\n")  # 空日记
    assert result.exit_code == 0, result.output
    entry = get_mood_by_date(date.today(), tmp_db)
    assert entry is not None
    assert entry.mood_score == 4


def test_record_with_note_and_tags(runner, tmp_db):
    result = invoke(
        runner,
        ["record", "5", "-n", "太棒了", "-t", "工作", "-t", "运动"],
        tmp_db,
        input_text="\n",
    )
    assert result.exit_code == 0, result.output
    entry = get_mood_by_date(date.today(), tmp_db)
    assert entry is not None
    assert entry.mood_score == 5
    assert entry.note == "太棒了"
    assert set(entry.tags) == {"工作", "运动"}


def test_record_specific_date(runner, tmp_db):
    result = invoke(
        runner,
        ["record", "3", "-d", "2026-01-15"],
        tmp_db,
        input_text="\n",
    )
    assert result.exit_code == 0, result.output
    entry = get_mood_by_date(date(2026, 1, 15), tmp_db)
    assert entry is not None
    assert entry.mood_score == 3


# ── 更新已有记录 ──────────────────────────────────────────────────

def test_record_force_update(runner, tmp_db):
    # 先写入评分 2
    invoke(runner, ["record", "2", "-d", "2026-02-01"], tmp_db, input_text="\n")
    # 强制覆盖为评分 5
    result = invoke(
        runner,
        ["record", "5", "-d", "2026-02-01", "--force"],
        tmp_db,
        input_text="\n",
    )
    assert result.exit_code == 0, result.output
    entry = get_mood_by_date(date(2026, 2, 1), tmp_db)
    assert entry is not None
    assert entry.mood_score == 5


# ── 错误处理 ──────────────────────────────────────────────────────

def test_record_invalid_score(runner, tmp_db):
    result = invoke(runner, ["record", "6"], tmp_db)
    assert result.exit_code != 0


def test_record_invalid_date(runner, tmp_db):
    result = invoke(runner, ["record", "3", "-d", "not-a-date"], tmp_db, input_text="\n")
    assert result.exit_code != 0
