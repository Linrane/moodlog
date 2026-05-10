"""
MoodLog - commands/stats.py
情绪统计面板、趋势图、月历视图。
v2：接入 i18n，统计面板文本使用 t()。
"""

from __future__ import annotations

from datetime import date, timedelta

import click
from rich import box
from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..database import get_moods_by_range, get_stats, get_all_moods, init_db
from ..config import config
from ..utils.display import (
    console, print_warning, score_text, month_calendar,
    streak_badge, mood_bar,
)
from ..utils.i18n import t


@click.command("trend")
@click.argument("days", type=int, required=False)
@click.option("--month", "-m", default=None, type=int, 
              help="查看指定月份（如 5 表示5月）")
@click.option("--year", "-y", default=None, type=int, 
              help="指定年份（与 --month 配合，默认当年）")
def trend_cmd(days, month, year):
    """📈 查看情绪趋势图。

    以 ASCII 图表形式展示情绪变化趋势，直观看到情绪波动。

    \b
    示例：
      moodlog trend              # 查看最近 7 天趋势（默认）
      moodlog trend 30           # 查看最近 30 天趋势
      moodlog trend --month 5    # 查看 5 月份趋势
      moodlog trend -m 5 -y 2025  # 查看 2025 年 5 月趋势

    \b
    提示：
      - 默认显示最近 7 天
      - 可以用 --month 查看任意月份
      - 图表使用 Rich 库绘制，支持现代终端
    """
    init_db()

    today = date.today()
    if month is not None:
        y = year or today.year
        start = date(y, month, 1)
        if month == 12:
            end = date(y + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(y, month + 1, 1) - timedelta(days=1)
        label = f"{y}年{month}月"
    else:
        n = days or config.default_trend_days
        end = today
        start = end - timedelta(days=n - 1)
        label = t("trend.title", days=n)

    entries = get_moods_by_range(start, end)
    if not entries:
        print_warning(t("trend.none", label=label))
        return

    from ..utils.chart import draw_trend
    draw_trend(entries, days=len(entries))


@click.command("stats")
@click.option("--month", "-m", default=None, type=int, 
              help="统计指定月份（1-12）")
@click.option("--year", "-y", default=None, type=int, 
              help="指定年份（默认当年）")
@click.option("--calendar", "-c", is_flag=True, default=False, 
              help="显示月历视图（直观看到每天的评分）")
def stats_cmd(month, year, calendar):
    """📊 查看情绪统计面板。

    显示丰富的统计分析，包括：
      - 总记录天数、平均分、最好/最差日子
      - 连续打卡天数（ streak ）
      - 情绪小结语（根据平均分自动生成）
      - 情绪分布图（1-5 分各多少天）
      - 高频标签统计
      - 月均情绪变化

    \b
    示例：
      moodlog stats              # 查看全部统计
      moodlog stats -c           # 查看统计 + 月历视图
      moodlog stats -m 5         # 查看 5 月份统计
      moodlog stats -y 2025      # 查看 2025 年统计
      moodlog stats -m 5 -y 2025 -c  # 查看指定年月 + 月历

    \b
    提示：
      - 月历视图会用颜色标记每天的心情
      - 没有记录的日期显示为空白
      - 标签统计只显示前 10 个高频标签
    """
    init_db()

    today = date.today()
    result = get_stats()

    if result.total_records == 0:
        print_warning(t("stats.none"))
        return

    # ── 总览面板 ────────────────────────────────────────────────
    overview = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    overview.add_column("指标", style="bold dim")
    overview.add_column("数值", justify="left")

    avg_score_int = round(result.avg_score)
    overview.add_row(t("stats.total_records"), f"[bold cyan]{result.total_records}[/bold cyan] 天")
    overview.add_row(
        t("stats.avg_mood"),
        f"{result.avg_score:.2f} / 5.00  {score_text(avg_score_int)}",
    )
    if result.max_date:
        overview.add_row(
            t("stats.best_day"),
            f"{result.max_date}  {score_text(result.max_score)}",
        )
    if result.min_date:
        overview.add_row(
            t("stats.worst_day"),
            f"{result.min_date}  {score_text(result.min_score)}",
        )

    console.print()
    console.print(Panel(
        overview,
        title=f"[bold cyan]{t('stats.overview_title')}[/bold cyan]",
        border_style="cyan",
    ))

    # ── 连续打卡 ───────────────────────────────────────────────
    streak = _calculate_streak(get_all_moods())
    console.print()
    console.print(Panel(streak_badge(streak), border_style="dim", padding=(0, 1)))

    # ── 情绪小结语 ──────────────────────────────────────────────
    _print_mood_summary(result)

    # ── 情绪分布 ────────────────────────────────────────────────
    all_entries = get_all_moods()
    from ..utils.chart import draw_score_distribution
    draw_score_distribution(all_entries)

    # ── 标签云 ─────────────────────────────────────────────────
    if result.tag_frequency:
        tag_table = Table(
            title=t("stats.tag_cloud", default="高频标签"),
            box=box.SIMPLE_HEAD,
            show_header=True,
            header_style="bold magenta",
        )
        tag_table.add_column("标签", style="magenta")
        tag_table.add_column("出现次数", justify="right")
        for tag, cnt in list(result.tag_frequency.items())[:10]:
            tag_table.add_row(f"#{tag}", str(cnt))
        console.print(tag_table)

    # ── 月均情绪 ────────────────────────────────────────────────
    if result.monthly_avg:
        m_table = Table(
            title=t("stats.monthly_avg", default="月均情绪"),
            box=box.SIMPLE_HEAD,
            show_header=True,
            header_style="bold green",
        )
        m_table.add_column("月份")
        m_table.add_column("平均分", justify="right")
        m_table.add_column("情绪")
        for ym, avg in result.monthly_avg.items():
            score_rounded = round(avg)
            m_table.add_row(ym, f"{avg:.2f}", score_text(score_rounded))
        console.print(m_table)

    # ── 月历视图 ────────────────────────────────────────────────
    if calendar:
        y = year or today.year
        m = month or today.month
        if month is not None:
            start = date(y, m, 1)
            end = date(y, m + 1, 1) - timedelta(days=1) if m < 12 else date(y, 12, 31)
        else:
            start = date(y, m, 1)
            end = today
        entries = get_moods_by_range(start, end)
        console.print()
        month_calendar(y, m, entries)


# ── 辅助函数 ──────────────────────────────────────────────────────────

def _calculate_streak(entries: list) -> int:
    """计算截至今天的连续打卡天数。"""
    if not entries:
        return 0
    from datetime import date as date_cls
    dates = sorted({e.date for e in entries}, reverse=True)
    today = date_cls.today()
    if dates[0] < today - timedelta(days=1):
        return 0
    streak = 0
    expected = dates[0]
    for d in dates:
        if d == expected:
            streak += 1
            expected = d - timedelta(days=1)
        else:
            break
    return streak


def _print_mood_summary(result) -> None:
    """根据统计数据输出一段情绪总结 Panel。"""
    from ..utils.i18n import mood_quote_i18n
    from rich.console import Group
    from rich.text import Text

    avg = result.avg_score
    total = result.total_records

    if avg >= 4.0:
        key = "stats.summary_high"
        color = "bright_green"
    elif avg >= 3.0:
        key = "stats.summary_mid"
        color = "yellow"
    elif avg >= 2.0:
        key = "stats.summary_low"
        color = "dark_orange"
    else:
        key = "stats.summary_very_low"
        color = "red"

    quote = mood_quote_i18n(round(avg))

    content = Text()
    content.append("😄  " if avg >= 4 else ("😐  " if avg >= 3 else ("😕  " if avg >= 2 else "😔  ")), style=f"bold {color}")
    content.append(t(key) + "\n", style=f"bold {color}")
    content.append(f"{t('stats.total_records', default='共')} {total}  {t('stats.days_suffix', default='天')}，{t('stats.avg_prefix', default='平均')} {avg:.1f} {t('stats.avg_suffix', default='分')}\n\n", style="dim")
    content.append(f"{quote}", style=f"italic {color}")

    console.print()
    console.print(Panel(
        content,
        title=f"[bold cyan]{t('stats.summary_title')}[/bold cyan]",
        border_style=color,
        padding=(0, 1),
    ))
