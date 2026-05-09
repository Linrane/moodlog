"""
MoodLog - utils/art.py
ASCII 艺术出场动画 & 视觉特效。
轻量化实现，仅依赖 Rich，无额外依赖。
"""

from __future__ import annotations

import random
import time
from typing import Callable

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.style import Style
from rich.text import Text

console = Console()

# ── MoodLog 专属 ASCII Logo ──────────────────────────────────
# 设计理念：一本展开的日记本，中间是心情符号

LOGO_FRAMES = [
    # Frame 1: 空白日记本轮廓
    r"""[dim]
     ╭─────────────────────────────────╮
     │                                 │
     │                                 │
     │                                 │
     │                                 │
     │                                 │
     ╰─────────────────────────────────╯
    [/dim]""",
    # Frame 2: 出现线条
    r"""[dim cyan]
     ╭─────────────────────────────────╮
     │  · · · · · · · · · · · · · ·  │
     │                                 │
     │                                 │
     │  · · · · · · · · · · · · · ·  │
     │                                 │
     ╰─────────────────────────────────╯
    [/dim cyan]""",
    # Frame 3: 出现文字轮廓
    r"""[cyan]
     ╭─────────────────────────────────╮
     │  · · · · · · · · · · · · · ·  │
     │                                 │
     │       M O O D   L O G          │
     │                                 │
     │  · · · · · · · · · · · · · ·  │
     │                                 │
     ╰─────────────────────────────────╯
    [/cyan]""",
    # Frame 4: 填色 + 装饰
    r"""[bold cyan]
     ╭─────────────────────────────────╮
     │  · · · · · · · · · · · · · ·  │
     │                                 │
     │       M O O D   L O G          │
     │       📔 ✨ 📔                 │
     │  · · · · · · · · · · · · · ·  │
     │                                 │
     ╰─────────────────────────────────╯
    [/bold cyan]""",
    # Frame 5: 完整版 + 副标题
    r"""[bold cyan]
     ╭─────────────────────────────────╮
     │  · · · · · · · · · · · · · ·  │
     │                                 │
     │       M O O D   L O G          │
     │       📔 ✨ 📔                 │
     │  · · · · · · · · · · · · · ·  │
     │                                 │
     │  终端心情日记 · 极简记录        │
     ╰─────────────────────────────────╯
    [/bold cyan]""",
]

# ── 心情符号进度动画帧 ───────────────────────────────────────
MOOD_PROGRESS_FRAMES = [
    "     ",
    "  📝  ",
    "  📝 💭  ",
    "  📝 💭 📔  ",
    "  📝 💭 📔 ✨  ",
]

# ── 分数选择时的 ASCII 装饰线 ─────────────────────────────────
SCORE_BORDER = {
    1: ("🔴", "red", "─── ▼ ───"),
    2: ("🟠", "dark_orange", "─── ▼ ───"),
    3: ("🟡", "yellow", "─── ▼ ───"),
    4: ("🟢", "green", "─── ▼ ───"),
    5: ("✨", "bright_green", "─── ▼ ───"),
}


def animate_logo(console: Console | None = None, fps: float = 0.35) -> None:
    """
    逐帧播放 MoodLog Logo 出场动画。
    在 1.5 秒内完成 5 帧揭示，轻量无阻塞。
    """
    c = console or Console()
    for frame in LOGO_FRAMES:
        c.print(frame)
        time.sleep(fps)
        c.print("\033[F" * frame.count("\n"), end="")
    # 最终清屏并打印完整版
    c.print(LOGO_FRAMES[-1])
    c.print()


def animate_loading(
    text: str = "正在加载",
    duration: float = 1.2,
    console: Console | None = None,
) -> None:
    """
    带心情符号轮播的"加载"动画（spinner 替代，纯 Rich 实现）。
    """
    c = console or Console()
    moods = ["😔", "😕", "😐", "🙂", "😄"]
    steps = max(int(duration / 0.15), 6)
    for i in range(steps):
        mood = moods[i % len(moods)]
        bar_len = min(i + 1, 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        line = f"[dim]{text}[/dim] {mood}  [cyan]{bar}[/cyan]"
        c.print(line, end="\r")
        time.sleep(duration / steps)
    c.print(f"[bold green]✓[/bold green] {text} 完成！{moods[-1]}")


def animate_mood_flash(
    score: int,
    console: Console | None = None,
) -> None:
    """
    记录成功后的"心情闪光"效果：
    用 Rich Live 在同一位置刷新 3 帧闪烁特效。
    """
    c = console or Console()
    emoji_list = ["😔", "😕", "😐", "🙂", "😄"]
    color_list = ["red", "dark_orange", "yellow", "green", "bright_green"]
    emoji = emoji_list[score - 1]
    color = color_list[score - 1]

    frames = [
        f"[bold {color}]    {emoji}  {emoji}  {emoji}  [/bold {color}]",
        f"[bold {color}]  ✨  {emoji}  ✨  {emoji}  ✨  [/bold {color}]",
        f"[bold {color}]    {emoji}  {emoji}  {emoji}  [/bold {color}]",
    ]
    for frame in frames:
        c.print(frame)
        time.sleep(0.2)
        # 回退行数（frame 只有 1 行，退 1 行）
        c.print("\033[F" * 1, end="")
    # 最终停留帧
    c.print(f"[bold {color}]  ✨ 记录成功！{emoji}  [/bold {color}]")


def score_picker_visual(console: Console | None = None) -> int:
    """
    可视化分数选择菜单：用 Rich Panel + 彩色排版，
    代替纯数字列表。返回用户选择的分数（1-5）。
    """
    from rich.prompt import Prompt

    c = console or Console()
    c.print()
    c.print("[bold cyan]╭─────────────────────────────────╮[/bold cyan]")
    c.print("[bold cyan]│       请选择今天的心情        │[/bold cyan]")
    c.print("[bold cyan]╰─────────────────────────────────╯[/bold cyan]")
    c.print()

    options = [
        ("1", "😔", "很低  —  今天很难",
         "red", "██░░░"),
        ("2", "😕", "偏低  —  有点低落",
         "dark_orange", "████░░░░░"),
        ("3", "😐", "一般  —  平平淡淡",
         "yellow", "██████░░░░"),
        ("4", "🙂", "不错  —  感觉挺好",
         "green", "████████░░"),
        ("5", "😄", "很棒  —  超级开心",
         "bright_green", "██████████"),
    ]
    for num, emoji, label, color, bar in options:
        line = (
            f"  [dim]╭─[/dim] [bold {color}]{num}[/bold {color}] "
            f"{emoji}  [bold {color}]{label}[/bold {color}]"
        )
        c.print(line)
        c.print(f"  [dim]╰──[/dim]   [dim {color}]{bar}[/dim {color}]")

    c.print()
    while True:
        raw = Prompt.ask("[bold cyan]输入评分 (1-5)[/bold cyan]")
        if raw.isdigit() and 1 <= int(raw) <= 5:
            return int(raw)
        c.print("[yellow]⚠  请输入 1 到 5 之间的整数。[/yellow]")


def pulse_border(text: str, color: str = "cyan", repeat: int = 2) -> None:
    """
    让一段文字在彩色边框内"脉冲"闪烁 repeat 次。
    利用 ANSI 回退行重写实现。
    """
    c = console or Console()
    for _ in range(repeat):
        # 亮
        c.print(Panel(text, border_style=f"bold {color}"))
        time.sleep(0.25)
        # 暗
        c.print(Panel(text, border_style=f"dim {color}"))
        time.sleep(0.25)


def _random_flourish() -> str:
    """返回随机心情装饰线（内部用）。"""
    return random.choice([
        "✨ 📔 ✨",
        "💭 ── 💭",
        "📝 ~ ☁️ ~ 📝",
        "─═─ 📔 ─═─",
        "· · · ◆ · · ·",
    ])


def splash_screen(console: Console | None = None) -> None:
    """
    完整出场画面：Logo 动画 + 加载条 + 欢迎语。
    在 `moodlog`（无子命令）启动时调用。
    """
    c = console or Console()

    # 第 1 阶段：Logo 逐帧
    c.print("\n" * 2)
    animate_logo(c, fps=0.25)

    # 第 2 阶段：加载进度条
    c.print()
    animate_loading("准备心情日记", duration=1.0, console=c)
    c.print()

    # 第 3 阶段：欢迎语 + 随机装饰
    flourish = _random_flourish()
    c.print(f"[dim cyan]{flourish}[/dim cyan]", justify="center")
    c.print("[dim]输入 [cyan]moodlog --help[/cyan] 查看所有命令[/dim]",
            justify="center")
    c.print()
