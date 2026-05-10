"""
MoodLog - utils/chart.py
使用 plotext 在终端绘制情绪趋势折线图。
降级方案：若 plotext 不可用，回退到纯 ASCII 柱状图。
"""
from __future__ import annotations

from datetime import date

from rich.console import Console
from rich.text import Text

from ..config import config
from ..models import MoodEntry
from .display import console, SCORE_COLORS

# 情绪折线图高度（行数）
_CHART_HEIGHT = 12
_CHART_BAR_WIDTH = 3


def _try_plotext(entries: list[MoodEntry], title: str) -> bool:
    """尝试用 plotext 绘图，成功返回 True。"""
    try:
        import plotext as plt  # type: ignore
    except ImportError:
        return False

    dates = [str(e.date) for e in entries]
    scores = [e.mood_score for e in entries]
    # 只取最后一位数字做 x 标签，避免堆叠
    x_labels = [d[-5:] for d in dates]  # "MM-DD"

    plt.clf()
    plt.theme("dark")
    plt.plot(scores, marker="braille", color="cyan+")
    plt.scatter(scores, marker="dot", color="green+")
    plt.xticks(list(range(1, len(dates) + 1)), x_labels)
    plt.yticks([1, 2, 3, 4, 5], ["😫1", "😔2", "😐3", "😊4", "🤩5"])
    plt.ylim(0.5, 5.5)
    plt.title(title)
    plt.xlabel("                        日期")
    plt.ylabel("            情绪值")
    plt.plot_size(110, _CHART_HEIGHT + 10)
    plt.show()
    return True


def _ascii_bar_chart(entries: list[MoodEntry], title: str) -> None:
    """纯 ASCII/Rich 柱状图降级方案。"""
    console.print(f"\n[bold cyan]{title}[/bold cyan]")
    console.print()

    bar_chars = "▁▂▃▄▅▆▇█"
    max_score = 5

    for e in entries:
        color = SCORE_COLORS.get(e.mood_score, "white")
        label = f"{e.date}"[-5:]  # MM-DD
        bar_len = round(e.mood_score / max_score * 24)
        bar = "█" * bar_len
        emoji = config.mood_emoji[e.mood_score - 1]
        line = Text()
        line.append(f"  {label} ", style="dim")
        line.append(bar, style=color)
        line.append(f" {emoji} {e.mood_score}", style=color)
        console.print(line)

    console.print()


def draw_trend(entries: list[MoodEntry], days: int) -> None:
    """绘制情绪趋势图（自动选择 plotext 或 ASCII 降级）。"""
    if not entries:
        from .display import print_warning
        print_warning("该时间段内没有记录数据。")
        return

    title = f"情绪趋势 - 近 {days} 天"
    if not _try_plotext(entries, title):
        _ascii_bar_chart(entries, title)


def draw_score_distribution(entries: list[MoodEntry]) -> None:
    """在终端显示情绪分布（1-5 每档的占比柱图）。"""
    if not entries:
        return

    from collections import Counter
    counter = Counter(e.mood_score for e in entries)
    total = len(entries)

    console.print("\n[bold cyan]情绪分布[/bold cyan]\n")
    for score in range(1, 6):
        cnt = counter.get(score, 0)
        pct = cnt / total * 100
        bar_len = round(pct / 100 * 30)
        color = SCORE_COLORS.get(score, "white")
        emoji = config.mood_emoji[score - 1]
        label = config.mood_labels[score - 1]
        bar = "█" * bar_len + "░" * (30 - bar_len)
        line = Text()
        line.append(f"  {score} {emoji} {label:<4} ", style="dim")
        line.append(bar, style=color)
        line.append(f"  {cnt:3d}次 ({pct:5.1f}%)", style="dim")
        console.print(line)
    console.print()
