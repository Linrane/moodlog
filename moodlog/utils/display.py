"""
MoodLog - utils/display.py
Rich 封装：统一的输出样式、颜色主题和格式化函数。
v3：接入 i18n 多语言支持。
"""
from __future__ import annotations

import random
from datetime import date
from typing import Any

from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.style import Style
from rich.table import Table
from rich.text import Text

from ..config import config
from ..models import MoodEntry
from ..utils.i18n import t, mood_quote_i18n

console = Console()

# ── 颜色主题 ─────────────────────────────────────────────
SCORE_COLORS = {
    1: "red",
    2: "dark_orange",
    3: "yellow",
    4: "green",
    5: "bright_green",
}

SCORE_BAR_CHAR = ""

# 情绪小结语（中文 fallback）
_MOOD_QUOTES: dict[int, list[str]] = {
    1: [
        "黑夜再长，黎明终将到来。🌑",
        "今天很难，但你撑过来了。",
        "低谷不是终点，只是路过。",
        "允许自己难过，然后继续前行。",
    ],
    2: [
        "有些日子就是平淡无奇，没关系。",
        "偶尔低落，是情绪在自我修复。",
        "休息也是一种前进。",
        "今天不够好，明天可以更好。☀️",
    ],
    3: [
        "平稳即是一种安定。",
        "不起波澜的日子也有它的价值。",
        "普通的一天，积累成非凡的人生。",
        "中间状态：既没有坏透，也可以更好。",
    ],
    4: [
        "今天状态不错，给自己点个赞！👍",
        "保持这股劲，明天继续！",
        "好情绪是最好的生产力。",
        "笑容是免费的，今天你用上了。😊",
    ],
    5: [
        "满满当当的一天，真棒！🎉",
        "这种感觉值得被记住。",
        "你发光的样子很迷人。✨",
        "把今天的能量存起来，以后用。🔋",
    ],
}


def mood_quote(score: int) -> str:
    """随机返回对应情绪分数的小结语（优先 i18n）。"""
    result = mood_quote_i18n(score)
    # mood_quote_i18n 失败时返回 key，此时用中文 fallback
    if result.startswith("stats.mood_quote"):
        quotes = _MOOD_QUOTES.get(score, ["今天也辛苦了。"])
        return random.choice(quotes)
    return result


def mood_bar(score: int, width: int = 20) -> Text:
    """返回带颜色的情绪进度条。"""
    color = SCORE_COLORS.get(score, "white")
    filled = round(score / 5 * width)
    bar = Text()
    bar.append(SCORE_BAR_CHAR * filled, style=color)
    bar.append("░" * (width - filled), style="dim")
    return bar


def score_text(score: int) -> Text:
    """带颜色的评分文字。"""
    color = SCORE_COLORS.get(score, "white")
    return Text(config.mood_display(score), style=Style(color=color, bold=True))


def section_rule(title: str = "", color: str = "cyan") -> None:
    """打印带标题的彩色分隔线。"""
    if title:
        console.print(Rule(f"[{color}]{title}[/{color}]", style=f"dim {color}"))
    else:
        console.print(Rule(style=f"dim {color}"))


def entry_table(entries: list[MoodEntry], title: str = "心情日记") -> Table:
    """将多条记录格式化为 Rich Table。"""
    table = Table(
        title=title,
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        show_lines=True,
        title_style="bold cyan",
        border_style="dim cyan",
    )
    table.add_column("日期", style="dim", width=12)
    table.add_column("心情", width=18)
    table.add_column("进度", width=22, no_wrap=True)
    table.add_column("标签", width=20)
    table.add_column("日记摘要", min_width=28)

    for e in entries:
        tags_text = Text()
        if e.tags:
            for i, t in enumerate(e.tags):
                if i > 0:
                    tags_text.append("  ")
                tags_text.append(f"#{t}", style="magenta")
        else:
            tags_text.append("—", style="dim")
        note_preview = Text()
        if e.note:
            if len(e.note) > 55:
                note_preview.append(e.note[:55] + "…")
            else:
                note_preview.append(e.note)
        else:
            note_preview.append("（无内容）", style="dim")
        table.add_row(
            str(e.date),
            score_text(e.mood_score),
            mood_bar(e.mood_score, width=18),
            tags_text,
            note_preview,
        )
    return table


def entry_detail(entry: MoodEntry, show_quote: bool = True) -> Panel:
    """单条记录的美化详情面板（双栏布局）。"""
    color = SCORE_COLORS.get(entry.mood_score, "white")

    left = Text()
    left.append("  心情评分\n", style="bold dim")
    left.append(f"  {config.mood_display(entry.mood_score)}\n", style=f"bold {color}")
    left.append("  ")
    left.append(mood_bar(entry.mood_score, width=16))
    left.append("\n\n")
    left.append("  日期        ", style="bold dim")
    left.append(f"{entry.date}\n", style="cyan")
    left.append("  记录时间  ", style="bold dim")
    left.append(f"{entry.created_at.strftime('%H:%M')}\n", style="dim")
    if entry.updated_at != entry.created_at:
        left.append("  更新时间  ", style="bold dim")
        left.append(f"{entry.updated_at.strftime('%H:%M')}\n", style="dim")
    if entry.tags:
        left.append("\n  标签\n", style="bold dim")
        for tag in entry.tags:
            left.append(f"  #{tag}", style="magenta")
            left.append("\n")

    right = Text()
    if entry.note:
        right.append("  📝 日记\n\n", style="bold dim")
        right.append(f"  {entry.note}\n", style="italic")
    else:
        right.append("  📝 日记\n\n", style="bold dim")
        right.append("  （今天没有写日记）\n", style="dim italic")

    if show_quote:
        right.append(f"\n  💬 {mood_quote(entry.mood_score)}\n", style=f"dim italic {color}")

    left_panel = Panel(left, box=box.SIMPLE, border_style=f"dim {color}", padding=(0, 0))
    right_panel = Panel(right, box=box.SIMPLE, border_style="dim", padding=(0, 0))

    columns = Columns([left_panel, right_panel], equal=True, expand=True)

    return Panel(
        columns,
        title=f"[bold {color}]📖 {entry.date}[/bold {color}]",
        border_style=color,
        padding=(0, 1),
        subtitle=f"[dim]{config.mood_display(entry.mood_score)}[/dim]",
    )


def streak_badge(streak: int) -> Text:
    """返回连续打卡天数的徽章文字（i18n）。"""
    t_obj = Text()
    if streak == 0:
        t_obj.append("  🌱 " + t("stats.streak_start"), style="dim")
    elif streak < 3:
        t_obj.append(f"  🔥  " + t("stats.streak_low", days=streak) + "  ", style="bold")
    elif streak < 7:
        t_obj.append(f"  🔥🔥  " + t("stats.streak_mid", days=streak) + "  ", style="bold")
    elif streak < 30:
        t_obj.append(f"  🔥🔥🔥  " + t("stats.streak_high", days=streak) + "  ", style="bold")
    else:
        t_obj.append(f"  🏆  " + t("stats.streak_legend", days=streak) + "  !!", style="bold bright_magenta")
    return t_obj


def month_calendar(year: int, month: int, entries: list[MoodEntry]) -> None:
    """在终端打印带情绪 emoji 的月历（i18n）。"""
    import calendar as cal_mod

    entry_map = {e.date: e for e in entries}

    title_str = t("calendar.month_title", year=year, month=month)
    section_rule(title_str, color="cyan")

    table = Table(
        box=box.MINIMAL_DOUBLE_HEAD,
        show_header=True,
        header_style="bold cyan",
        border_style="dim cyan",
        show_lines=True,
    )
    weekdays = ["一", "二", "三", "四", "五", "六", "日"]
    # 尝试从 i18n 读取星期名（英文环境下会是 Mon~Sun）
    weekday_key = "calendar.weekdays"
    translations = __import__("moodlog.utils.i18n", fromlist=["_get_translations"])._get_translations
    try:
        wd = translations().get("calendar", {}).get("weekdays", weekdays)
    except Exception:
        wd = weekdays
    for day_name in wd:
        table.add_column(day_name, justify="center", width=7, no_wrap=True)

    cal = cal_mod.monthcalendar(year, month)
    today = date.today()
    for week in cal:
        cells: list[Any] = []
        for d in week:
            if d == 0:
                cells.append("")
            else:
                day_date = date(year, month, d)
                entry = entry_map.get(day_date)
                if entry:
                    color = SCORE_COLORS.get(entry.mood_score, "white")
                    emoji = config.mood_emoji[entry.mood_score - 1]
                    t = Text(justify="center")
                    t.append(f"{d:2d}", style=f"bold {color}")
                    t.append(emoji)
                    cells.append(t)
                elif day_date == today:
                    t = Text(justify="center")
                    t.append(f"{d:2d} ●", style="bold yellow")
                    cells.append(t)
                elif day_date > today:
                    cells.append(Text(f"{d:2d}", style="dim", justify="center"))
                else:
                    cells.append(Text(f"{d:2d} ·", style="dim", justify="center"))
        table.add_row(*cells)

    console.print(table)
    recorded = len(entry_map)
    total_days = cal_mod.monthrange(year, month)[1]
    pct = recorded / total_days * 100 if total_days > 0 else 0
    console.print(
        f"\n  "
        + t("calendar.completion", recorded=recorded, total=total_days, pct=f"{pct:.0f}")
        + "\n"
    )


def today_empty_card() -> Panel:
    """今天还没有记录时显示的空白引导卡片。"""
    today = date.today()
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekdays[today.weekday()]

    content = Text(justify="center")
    content.append("\n")
    content.append("今天还没有记录 ✨\n\n", style="bold dim")
    content.append(f"  {today}  {weekday}\n\n", style="cyan")
    content.append("  现在就写下今天的心情：\n\n", style="dim")
    content.append("  moodlog record 4\n", style="bold green")
    content.append("  moodlog record\n\n", style="bold green")

    return Panel(
        Align(content, "center"),
        title="[bold cyan]📔 今日日记[/bold cyan]",
        border_style="dim cyan",
        padding=(1, 4),
    )


def print_success(msg: str) -> None:
    console.print(f"[bold green]✓[/bold green] {msg}")


def print_warning(msg: str) -> None:
    console.print(f"[bold yellow]⚠[/bold yellow]  {msg}")


def print_error(msg: str) -> None:
    console.print(f"[bold red]✗[/bold red] {msg}")


def print_info(msg: str) -> None:
    console.print(f"[bold blue]ℹ[/bold blue]  {msg}")
