"""
MoodLog - database.py
数据库初始化、连接管理和所有 CRUD 操作。
使用标准库 sqlite3，封装为简洁的函数接口。
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Generator

from .config import config
from .models import MoodEntry, StatsResult

# ── Python 3.12+ 日期适配器（消除 DeprecationWarning）──────────────
def _adapt_date(d: date) -> str:
    return d.isoformat()

def _adapt_datetime(dt: datetime) -> str:
    return dt.isoformat()

def _convert_date(s: bytes) -> date:
    return date.fromisoformat(s.decode())

def _convert_datetime(s: bytes) -> datetime:
    return datetime.fromisoformat(s.decode())

sqlite3.register_adapter(date, _adapt_date)
sqlite3.register_adapter(datetime, _adapt_datetime)
sqlite3.register_converter("DATE", _convert_date)
sqlite3.register_converter("DATETIME", _convert_datetime)

# ── DDL ─────────────────────────────────────────────────────────
_CREATE_MOODS = """
CREATE TABLE IF NOT EXISTS moods (
    id          INTEGER  PRIMARY KEY AUTOINCREMENT,
    date        DATE     NOT NULL UNIQUE,
    mood_score  INTEGER  NOT NULL CHECK(mood_score BETWEEN 1 AND 5 OR mood_score = 100),
    note        TEXT     NOT NULL DEFAULT '',
    created_at  DATETIME NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at  DATETIME NOT NULL DEFAULT (datetime('now','localtime'))
);
"""

_CREATE_TAGS = """
CREATE TABLE IF NOT EXISTS tags (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    mood_id  INTEGER NOT NULL REFERENCES moods(id) ON DELETE CASCADE,
    name     TEXT    NOT NULL,
    UNIQUE(mood_id, name)
);
"""

_CREATE_IDX_DATE = "CREATE INDEX IF NOT EXISTS idx_moods_date ON moods(date);"
_CREATE_IDX_TAG  = "CREATE INDEX IF NOT EXISTS idx_tags_name  ON tags(name);"


# ── 连接上下文管理器 ──────────────────────────────────────────────

def get_db_path() -> Path:
    return config.db_path


@contextmanager
def get_connection(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """提供一个自动提交/回滚的数据库连接上下文。"""
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")  # 提升并发写性能
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── 初始化 ────────────────────────────────────────────────────────



def _migrate_moods_table(conn: sqlite3.Connection) -> None:
    """迁移 moods 表：移除旧 CHECK 约束（如果存在）。"""
    try:
        conn.execute("INSERT INTO moods (date, mood_score) VALUES ('2099-01-01', 100)")
        conn.execute("DELETE FROM moods WHERE date = '2099-01-01'")
        return  # 无需迁移
    except sqlite3.IntegrityError:
        pass  # 需要迁移

    # 执行迁移
    conn.execute("ALTER TABLE moods RENAME TO moods_old")
    conn.execute(_CREATE_MOODS)
    conn.execute("""
        INSERT INTO moods (id, date, mood_score, note, created_at, updated_at)
        SELECT id, date, mood_score, note, created_at, updated_at FROM moods_old
    """)
    conn.execute("DROP TABLE moods_old")

def init_db(db_path: Path | None = None) -> None:
    """创建数据表（幂等操作），并执行必要的迁移。"""
    with get_connection(db_path) as conn:
        conn.execute(_CREATE_MOODS)
        conn.execute(_CREATE_TAGS)
        conn.execute(_CREATE_IDX_DATE)
        conn.execute(_CREATE_IDX_TAG)
        _migrate_moods_table(conn)


# ── 写操作 ────────────────────────────────────────────────────────

def insert_or_update_mood(
    record_date: date,
    score: int,
    note: str,
    tags: list[str],
    db_path: Path | None = None,
) -> tuple[MoodEntry, bool]:
    """
    插入或更新一条心情记录。
    返回 (MoodEntry, is_new)：is_new=True 表示新建，False 表示更新。
    """
    now = datetime.now().replace(microsecond=0)
    with get_connection(db_path) as conn:
        cur = conn.execute("SELECT id, created_at FROM moods WHERE date = ?", (record_date,))
        existing = cur.fetchone()
        is_new = existing is None

        if is_new:
            cur = conn.execute(
                "INSERT INTO moods (date, mood_score, note, created_at, updated_at) VALUES (?,?,?,?,?)",
                (record_date, score, note, now, now),
            )
            mood_id = cur.lastrowid
            created_at = now
        else:
            mood_id = existing["id"]
            created_at = existing["created_at"]
            conn.execute(
                "UPDATE moods SET mood_score=?, note=?, updated_at=? WHERE id=?",
                (score, note, now, mood_id),
            )
            # 清除旧标签，重新写入
            conn.execute("DELETE FROM tags WHERE mood_id=?", (mood_id,))

        # 写入标签（去重）
        clean_tags = list(dict.fromkeys(t.strip() for t in tags if t.strip()))
        for tag in clean_tags:
            conn.execute(
                "INSERT OR IGNORE INTO tags (mood_id, name) VALUES (?,?)",
                (mood_id, tag),
            )

    entry = MoodEntry(
        id=mood_id,
        date=record_date,
        mood_score=score,
        note=note,
        created_at=created_at if isinstance(created_at, datetime) else datetime.fromisoformat(str(created_at)),
        updated_at=now,
        tags=clean_tags,
    )
    return entry, is_new


def delete_mood(record_date: date, db_path: Path | None = None) -> bool:
    """删除指定日期的记录。返回是否真的删了。"""
    with get_connection(db_path) as conn:
        cur = conn.execute("DELETE FROM moods WHERE date = ?", (record_date,))
        return cur.rowcount > 0


# ── 读操作 ────────────────────────────────────────────────────────

def _row_to_entry(row: sqlite3.Row, tags: list[str]) -> MoodEntry:
    return MoodEntry(
        id=row["id"],
        date=date.fromisoformat(str(row["date"])),
        mood_score=row["mood_score"],
        note=row["note"] or "",
        created_at=datetime.fromisoformat(str(row["created_at"])),
        updated_at=datetime.fromisoformat(str(row["updated_at"])),
        tags=tags,
    )


def _fetch_tags_for_ids(conn: sqlite3.Connection, mood_ids: list[int]) -> dict[int, list[str]]:
    """批量获取多条记录的标签，避免 N+1 查询。"""
    if not mood_ids:
        return {}
    placeholders = ",".join("?" * len(mood_ids))
    rows = conn.execute(
        f"SELECT mood_id, name FROM tags WHERE mood_id IN ({placeholders}) ORDER BY id",
        mood_ids,
    ).fetchall()
    result: dict[int, list[str]] = {mid: [] for mid in mood_ids}
    for row in rows:
        result[row["mood_id"]].append(row["name"])
    return result


def get_mood_by_date(record_date: date, db_path: Path | None = None) -> MoodEntry | None:
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM moods WHERE date = ?", (record_date,)).fetchone()
        if row is None:
            return None
        tags_map = _fetch_tags_for_ids(conn, [row["id"]])
        return _row_to_entry(row, tags_map.get(row["id"], []))


def get_moods_by_range(
    start: date,
    end: date,
    db_path: Path | None = None,
) -> list[MoodEntry]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM moods WHERE date BETWEEN ? AND ? ORDER BY date ASC",
            (start, end),
        ).fetchall()
        if not rows:
            return []
        ids = [r["id"] for r in rows]
        tags_map = _fetch_tags_for_ids(conn, ids)
        return [_row_to_entry(r, tags_map.get(r["id"], [])) for r in rows]


def search_moods(keyword: str, db_path: Path | None = None) -> list[MoodEntry]:
    """对 note 字段进行模糊搜索，同时也搜索标签名。"""
    with get_connection(db_path) as conn:
        # 搜索日记内容
        rows_note = conn.execute(
            "SELECT * FROM moods WHERE note LIKE ? ORDER BY date DESC",
            (f"%{keyword}%",),
        ).fetchall()
        # 搜索标签
        tag_mood_ids = {
            r["mood_id"]
            for r in conn.execute(
                "SELECT DISTINCT mood_id FROM tags WHERE name LIKE ?",
                (f"%{keyword}%",),
            ).fetchall()
        }
        # 合并去重
        seen = {r["id"] for r in rows_note}
        extra_ids = [mid for mid in tag_mood_ids if mid not in seen]
        extra_rows = []
        if extra_ids:
            placeholders = ",".join("?" * len(extra_ids))
            extra_rows = conn.execute(
                f"SELECT * FROM moods WHERE id IN ({placeholders}) ORDER BY date DESC",
                extra_ids,
            ).fetchall()

        all_rows = list(rows_note) + extra_rows
        all_rows.sort(key=lambda r: r["date"], reverse=True)
        all_ids = [r["id"] for r in all_rows]
        tags_map = _fetch_tags_for_ids(conn, all_ids)
        return [_row_to_entry(r, tags_map.get(r["id"], [])) for r in all_rows]


def get_all_moods(db_path: Path | None = None) -> list[MoodEntry]:
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM moods ORDER BY date ASC").fetchall()
        if not rows:
            return []
        ids = [r["id"] for r in rows]
        tags_map = _fetch_tags_for_ids(conn, ids)
        return [_row_to_entry(r, tags_map.get(r["id"], [])) for r in rows]


def get_stats(db_path: Path | None = None) -> StatsResult:
    """计算汇总统计数据。"""
    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*)           AS total,
                AVG(mood_score)    AS avg_score,
                MAX(mood_score)    AS max_score,
                MIN(mood_score)    AS min_score
            FROM moods
            """
        ).fetchone()

        total = row["total"] or 0
        avg_score = round(float(row["avg_score"] or 0), 2)
        max_score = row["max_score"] or 0
        min_score = row["min_score"] or 0

        max_row = conn.execute(
            "SELECT date FROM moods WHERE mood_score = ? ORDER BY date DESC LIMIT 1",
            (max_score,),
        ).fetchone()
        min_row = conn.execute(
            "SELECT date FROM moods WHERE mood_score = ? ORDER BY date ASC LIMIT 1",
            (min_score,),
        ).fetchone()

        tag_rows = conn.execute(
            "SELECT name, COUNT(*) AS cnt FROM tags GROUP BY name ORDER BY cnt DESC LIMIT 20"
        ).fetchall()
        tag_freq = {r["name"]: r["cnt"] for r in tag_rows}

        monthly_rows = conn.execute(
            """
            SELECT strftime('%Y-%m', date) AS ym, AVG(mood_score) AS avg
            FROM moods
            GROUP BY ym
            ORDER BY ym ASC
            """
        ).fetchall()
        monthly_avg = {r["ym"]: round(float(r["avg"]), 2) for r in monthly_rows}

    return StatsResult(
        total_records=total,
        avg_score=avg_score,
        max_score=max_score,
        max_date=date.fromisoformat(str(max_row["date"])) if max_row else None,
        min_score=min_score,
        min_date=date.fromisoformat(str(min_row["date"])) if min_row else None,
        tag_frequency=tag_freq,
        monthly_avg=monthly_avg,
    )
