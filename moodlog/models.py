"""
MoodLog - models.py
纯 Python 数据类，与数据库无关，用于在层之间传递数据。
不引入任何 ORM，保持轻量。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class Tag:
    id: int | None
    mood_id: int
    name: str


@dataclass
class MoodEntry:
    """一条心情记录，包含关联标签。"""
    id: int | None
    date: date
    mood_score: int          # 1-5
    note: str                # 可为空字符串
    created_at: datetime
    updated_at: datetime
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not (1 <= self.mood_score <= 5):
            raise ValueError(f"mood_score 必须在 1-5 之间，收到: {self.mood_score}")


@dataclass
class StatsResult:
    """统计汇总结果。"""
    total_records: int
    avg_score: float
    max_score: int
    max_date: date | None
    min_score: int
    min_date: date | None
    tag_frequency: dict[str, int]   # {标签名: 出现次数}
    monthly_avg: dict[str, float]   # {"2026-05": 3.7, ...}
