"""
test_stats.py
统计与趋势相关的单元测试。
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from moodlog.database import init_db, insert_or_update_mood, get_stats
from moodlog.models import StatsResult


@pytest.fixture
def db_with_data(tmp_path) -> Path:
    """预填 10 条测试数据的数据库。"""
    db = tmp_path / "stats_test.db"
    init_db(db)
    test_data = [
        (date(2026, 4, 1), 3, "四月开始", ["工作"]),
        (date(2026, 4, 10), 2, "有点累", ["工作", "压力"]),
        (date(2026, 4, 20), 4, "周末愉快", ["休息", "社交"]),
        (date(2026, 5, 1), 5, "五一假期", ["旅行", "社交"]),
        (date(2026, 5, 5), 5, "很棒的一天", ["运动"]),
        (date(2026, 5, 6), 1, "最糟糕的一天", ["压力"]),
        (date(2026, 5, 7), 3, "恢复中", []),
        (date(2026, 5, 8), 4, "好转了", ["工作"]),
        (date(2026, 5, 9), 4, "稳定", ["工作", "运动"]),
        (date(2026, 5, 10), 5, "冲鸭", ["编程"]),
    ]
    for d, score, note, tags in test_data:
        insert_or_update_mood(d, score, note, tags, db)
    return db


def test_stats_total_records(db_with_data):
    stats = get_stats(db_with_data)
    assert stats.total_records == 10


def test_stats_avg_score(db_with_data):
    stats = get_stats(db_with_data)
    expected_avg = (3 + 2 + 4 + 5 + 5 + 1 + 3 + 4 + 4 + 5) / 10
    assert abs(stats.avg_score - expected_avg) < 0.01


def test_stats_max_min(db_with_data):
    stats = get_stats(db_with_data)
    assert stats.max_score == 5
    assert stats.min_score == 1
    assert stats.min_date == date(2026, 5, 6)


def test_stats_tag_frequency(db_with_data):
    stats = get_stats(db_with_data)
    # "工作" 出现在 2026-04-01, 2026-04-10, 2026-05-08, 2026-05-09 → 4次
    assert stats.tag_frequency.get("工作") == 4
    # "社交" 出现 2次
    assert stats.tag_frequency.get("社交") == 2


def test_stats_monthly_avg(db_with_data):
    stats = get_stats(db_with_data)
    # 四月：(3+2+4)/3 ≈ 3.0
    assert "2026-04" in stats.monthly_avg
    assert abs(stats.monthly_avg["2026-04"] - (3 + 2 + 4) / 3) < 0.01
    # 五月：(5+5+1+3+4+4+5)/7 ≈ 3.86
    assert "2026-05" in stats.monthly_avg
    expected_may = (5 + 5 + 1 + 3 + 4 + 4 + 5) / 7
    assert abs(stats.monthly_avg["2026-05"] - expected_may) < 0.01


def test_stats_tag_ordering(db_with_data):
    """标签应按频率降序排列，"工作"最高。"""
    stats = get_stats(db_with_data)
    tags_list = list(stats.tag_frequency.keys())
    if len(tags_list) >= 2:
        # 最高频标签应该是"工作"
        assert tags_list[0] == "工作"
