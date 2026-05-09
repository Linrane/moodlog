"""
test_database.py
数据库层单元测试 — 使用内存数据库，不产生任何磁盘文件。
"""
from __future__ import annotations

import tempfile
from datetime import date, datetime
from pathlib import Path

import pytest

from moodlog.database import (
    init_db, insert_or_update_mood, get_mood_by_date,
    get_moods_by_range, delete_mood, search_moods, get_stats,
)
from moodlog.models import MoodEntry


@pytest.fixture
def tmp_db(tmp_path) -> Path:
    """每个测试用独立的临时数据库文件。"""
    db = tmp_path / "test_moodlog.db"
    init_db(db)
    return db


# ── 插入与查询 ────────────────────────────────────────────────────

def test_insert_new_entry(tmp_db):
    d = date(2026, 5, 1)
    entry, is_new = insert_or_update_mood(d, 4, "测试日记", ["工作", "编程"], tmp_db)
    assert is_new is True
    assert entry.mood_score == 4
    assert entry.note == "测试日记"
    assert set(entry.tags) == {"工作", "编程"}


def test_get_mood_by_date(tmp_db):
    d = date(2026, 5, 2)
    insert_or_update_mood(d, 3, "普通的一天", [], tmp_db)
    entry = get_mood_by_date(d, tmp_db)
    assert entry is not None
    assert entry.date == d
    assert entry.mood_score == 3


def test_get_mood_by_date_not_found(tmp_db):
    result = get_mood_by_date(date(2000, 1, 1), tmp_db)
    assert result is None


def test_update_existing_entry(tmp_db):
    d = date(2026, 5, 3)
    insert_or_update_mood(d, 2, "原始内容", ["A"], tmp_db)
    entry, is_new = insert_or_update_mood(d, 5, "更新内容", ["B", "C"], tmp_db)
    assert is_new is False
    assert entry.mood_score == 5
    assert entry.note == "更新内容"
    assert set(entry.tags) == {"B", "C"}
    # 确认数据库中确实只有一条记录（UNIQUE constraint）
    from moodlog.database import get_connection
    with get_connection(tmp_db) as conn:
        count = conn.execute("SELECT COUNT(*) FROM moods WHERE date=?", (d,)).fetchone()[0]
    assert count == 1


def test_tags_deduplication(tmp_db):
    d = date(2026, 5, 4)
    entry, _ = insert_or_update_mood(d, 3, "", ["工作", "工作", "运动"], tmp_db)
    assert len(entry.tags) == 2
    assert set(entry.tags) == {"工作", "运动"}


# ── 范围查询 ──────────────────────────────────────────────────────

def test_get_moods_by_range(tmp_db):
    dates = [date(2026, 5, i) for i in range(1, 8)]
    for i, d in enumerate(dates, start=1):
        insert_or_update_mood(d, (i % 5) + 1, f"第{i}天", [], tmp_db)

    entries = get_moods_by_range(date(2026, 5, 2), date(2026, 5, 5), tmp_db)
    assert len(entries) == 4
    assert entries[0].date == date(2026, 5, 2)
    assert entries[-1].date == date(2026, 5, 5)


def test_get_moods_by_range_empty(tmp_db):
    result = get_moods_by_range(date(2026, 1, 1), date(2026, 1, 31), tmp_db)
    assert result == []


# ── 搜索 ──────────────────────────────────────────────────────────

def test_search_by_note(tmp_db):
    insert_or_update_mood(date(2026, 5, 10), 4, "完成了重要项目", [], tmp_db)
    insert_or_update_mood(date(2026, 5, 11), 2, "普通的一天", [], tmp_db)
    results = search_moods("重要", tmp_db)
    assert len(results) == 1
    assert results[0].date == date(2026, 5, 10)


def test_search_by_tag(tmp_db):
    insert_or_update_mood(date(2026, 5, 12), 5, "", ["健身", "运动"], tmp_db)
    insert_or_update_mood(date(2026, 5, 13), 3, "", ["工作"], tmp_db)
    results = search_moods("健身", tmp_db)
    assert len(results) == 1
    assert results[0].date == date(2026, 5, 12)


def test_search_no_result(tmp_db):
    insert_or_update_mood(date(2026, 5, 14), 3, "日常", [], tmp_db)
    results = search_moods("不存在的关键词xyz", tmp_db)
    assert results == []


# ── 删除 ──────────────────────────────────────────────────────────

def test_delete_mood(tmp_db):
    d = date(2026, 5, 20)
    insert_or_update_mood(d, 3, "", [], tmp_db)
    assert delete_mood(d, tmp_db) is True
    assert get_mood_by_date(d, tmp_db) is None


def test_delete_nonexistent(tmp_db):
    assert delete_mood(date(2000, 1, 1), tmp_db) is False


# ── 统计 ──────────────────────────────────────────────────────────

def test_stats_empty(tmp_db):
    stats = get_stats(tmp_db)
    assert stats.total_records == 0
    assert stats.avg_score == 0.0


def test_stats_correct(tmp_db):
    insert_or_update_mood(date(2026, 5, 1), 5, "", ["A"], tmp_db)
    insert_or_update_mood(date(2026, 5, 2), 3, "", ["A", "B"], tmp_db)
    insert_or_update_mood(date(2026, 5, 3), 1, "", ["B"], tmp_db)

    stats = get_stats(tmp_db)
    assert stats.total_records == 3
    assert abs(stats.avg_score - (5 + 3 + 1) / 3) < 0.01
    assert stats.max_score == 5
    assert stats.min_score == 1
    assert stats.tag_frequency.get("A") == 2
    assert stats.tag_frequency.get("B") == 2


def test_stats_tag_cascade_delete(tmp_db):
    """删除 mood 条目后，其标签也应该被级联删除。"""
    d = date(2026, 5, 25)
    insert_or_update_mood(d, 4, "", ["临时标签"], tmp_db)
    delete_mood(d, tmp_db)
    stats = get_stats(tmp_db)
    assert "临时标签" not in stats.tag_frequency
