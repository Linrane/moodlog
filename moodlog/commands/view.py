"""
MoodLog - commands/view.py
查看日记：今天 / 指定日期 / 日期范围 / 全文搜索。
v2：接入 i18n。
"""
from __future__ import annotations

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
    """📅 查看今天的心情记录。

    \b
    示例：
      moodlog today

    \b
    提示：
      如果今天还没有记录，会提示你使用 'moodlog record' 记录。
      查看其他日期请使用 'moodlog view <日期>'。
    """
    init_db()
    entry = get_mood_by_date(date.today())
    if entry is None:
        from ..utils.display import today_empty_card
        console.print()
        console.print(today_empty_card())
        return
    console.print()
    console.print(entry_detail(entry))


@click.command("view")
@click.argument("target_date", required=False)
@click.option("--from", "date_from", default=None, 
              help="开始日期（YYYY-MM-DD）")
@click.option("--to", "date_to", default=None, 
              help="结束日期（YYYY-MM-DD）")
@click.option("--last", default=None, type=int, 
              help="最近 N 天（例如：--last 30）")
@click.option("--search", "-s", default=None, 
              help="关键词搜索（搜索日记内容和标签）")
def view_cmd(target_date, date_from, date_to, last, search):
    """🔍 查看历史日记。

    支持多种查看方式：按日期、按范围、按关键词搜索。

    \b
    示例：
      moodlog view                          # 查看最近 7 天
      moodlog view 2026-05-09              # 查看某一天
      moodlog view --last 14               # 最近 14 天
      moodlog view --last 30               # 最近 30 天
      moodlog view --from 2026-05-01 --to 2026-05-31  # 指定范围
      moodlog view -s 工作                 # 搜索关键词"工作"
      moodlog view -s "项目完成"           # 搜索完整短语

    \b
    提示：
      - 不指定任何参数时，默认显示最近 7 天
      - 搜索功能会匹配日记内容和标签
      - 日期格式必须是 YYYY-MM-DD（如 2026-05-09）
    """
    init_db()

    # 关键词搜索模式
    if search:
        entries = search_moods(search)
        if not entries:
            print_warning(t("view.no_results", default=f"没有找到包含「{search}」的记录 🔍"))
            return
        console.print()
        console.print(entry_table(entries, title=t("view.search_title", keyword=search, default=f"搜索结果：{search}")))
        return

    # 单日查看
    if target_date:
        try:
            d = date.fromisoformat(target_date)
        except ValueError:
            print_error(f"日期格式不对哦 😅  应该是 YYYY-MM-DD，例如 2026-05-11")
            return
        entry = get_mood_by_date(d)
        if entry is None:
            print_warning(f"{d} 还没有记录 📭  用 [bold]moodlog record[/bold] 补记一下？")
        else:
            console.print()
            console.print(entry_detail(entry))
        return

    # 最近 N 天
    if last is not None:
        if last <= 0:
            print_error("天数得是正整数哦，比如 --last 7 或 --last 30 🙃")
            return
        if last > 3650:
            print_error("天数太长了，最多支持 10 年（约 3650 天）的查询 😅  试试小一点的数字？")
            return
        end = date.today()
        start = end - timedelta(days=last - 1)
    elif date_from or date_to:
        try:
            start = date.fromisoformat(date_from) if date_from else date(2000, 1, 1)
            end = date.fromisoformat(date_to) if date_to else date.today()
        except ValueError:
            print_error("日期格式不对哦 😅  应该是 YYYY-MM-DD，例如 2026-05-01")
            return
        if start > end:
            print_error("开始日期不能晚于结束日期哦 🙃")
            return
    else:
        # 默认查看最近 7 天
        end = date.today()
        start = end - timedelta(days=6)

    entries = get_moods_by_range(start, end)
    if not entries:
        print_warning(f"{start} 到 {end} 之间没有记录 📭  用 [bold]moodlog record[/bold] 记录一下吧~")
        return
    console.print()
    console.print(entry_table(entries, title=t("view.records_from", date=start, default=f"{start} 以来的记录")))
