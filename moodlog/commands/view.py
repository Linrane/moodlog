"""
MoodLog - commands/view.py
查看日记：今天 / 指定日期 / 日期范围 / 全文搜索。
v2：接入 i18n。
"""
from __future__ import annotations

import sys
from datetime import date, timedelta

import click

from ..database import (
    get_mood_by_date, get_moods_by_range, search_moods, init_db,
)
from ..utils.display import (
    console, print_warning, print_error, entry_table, entry_detail,
)
from ..utils.i18n import t


@click.command("today")
def today_cmd():
    """📅 查看今天的心情记录。"""
    init_db()
    entry = get_mood_by_date(date.today())
    if entry is None:
        print_warning(t("view.today_none"))
        return
    console.print()
    console.print(entry_detail(entry))


@click.command("view")
@click.argument("target_date", required=False)
@click.option("--from", "date_from", default=None, help="开始日期（YYYY-MM-DD）")
@click.option("--to", "date_to", default=None, help="结束日期（YYYY-MM-DD）")
@click.option("--last", default=None, type=int, help="最近 N 天")
@click.option("--search", "-s", default=None, help="关键词搜索（日记内容 + 标签）")
def view_cmd(target_date, date_from, date_to, last, search):
    """🔍 查看历史日记。

    \b
    示例：
      moodlog view 2026-05-09        # 查看某天
      moodlog view --last 14         # 最近14天
      moodlog view --from 2026-05-01 --to 2026-05-31
      moodlog view -s 工作           # 搜索关键词
    """
    init_db()

    # 关键词搜索模式
    if search:
        entries = search_moods(search)
        if not entries:
            print_warning(t("view.no_records", keyword=search))
            return
        console.print()
        console.print(entry_table(entries, title=t("view.search_title", keyword=search)))
        return

    # 单日查看
    if target_date:
        try:
            d = date.fromisoformat(target_date)
        except ValueError:
            print_error(t("record.messages.date_format_error", date=target_date))
            sys.exit(1)
        entry = get_mood_by_date(d)
        if entry is None:
            print_warning(t("view.no_record_on", date=d))
        else:
            console.print()
            console.print(entry_detail(entry))
        return

    # 最近 N 天
    if last is not None:
        end = date.today()
        start = end - timedelta(days=last - 1)
    elif date_from or date_to:
        try:
            start = date.fromisoformat(date_from) if date_from else date(2000, 1, 1)
            end = date.fromisoformat(date_to) if date_to else date.today()
        except ValueError as e:
            print_error(t("record.messages.date_format_error", date=str(e)))
            sys.exit(1)
    else:
        # 默认查看最近 7 天
        end = date.today()
        start = end - timedelta(days=6)

    entries = get_moods_by_range(start, end)
    if not entries:
        print_warning(t("view.no_records_in_range", start=start, end=end))
        return
    console.print()
    console.print(entry_table(entries, title=t("view.records_from", date=start)))
