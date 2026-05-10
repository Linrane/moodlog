"""
MoodLog - utils/art.py
CLI 出场动画 & 视觉特效。
设计风格：复古像素风（Claude Code 风格）+ 现代动画
"""

from __future__ import annotations

import random
import sys
import time
from typing import Callable

from rich.console import Console

console = Console(markup=True)

# ── 复古像素 Logo ─────────────────────────────────────────
# 灵感：Claude Code 风格 - 大号像素字母

PIXEL_LOGO = """
[bold cyan]

    ███╗   ███╗ ██████╗  ██████╗ ██████╗ ██╗      ██████╗  ██████╗
    ████╗ ████║██╔═══██╗██╔═══██╗██╔══██╗██║     ██╔═══██╗██╔════╝
    ██╔████╔██║██║   ██║██║   ██║██║  ██║██║     ██║   ██║██║  ███╗
    ██║╚██╔╝██║██║   ██║██║   ██║██║  ██║██║     ██║   ██║██║   ██║
    ██║ ╚═╝ ██║╚██████╔╝╚██████╔╝██████╔╝███████╗╚██████╔╝╚██████╔╝
    ╚═╝     ╚═╝ ╚═════╝  ╚═════╝ ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝

[/bold cyan]
"""

# ── 紧凑版 Logo ───────────────────────────────────────────

PIXEL_LOGO_COMPACT = """
[bold cyan]

  ███╗   ███╗ ██████╗  ██████╗ ██████╗ ██╗      ██████╗  ██████╗
  ████╗ ████║██╔═══██╗██╔═══██╗██╔══██╗██║     ██╔═══██╗██╔════╝
  ██╔████╔██║██║   ██║██║   ██║██║  ██║██║     ██║   ██║██║  ███╗
  ██║╚██╔╝██║██║   ██║██║   ██║██║  ██║██║     ██║   ██║██║   ██║
  ██║ ╚═╝ ██║╚██████╔╝╚██████╔╝██████╔╝███████╗╚██████╔╝╚██████╔╝
  ╚═╝     ╚═╝ ╚═════╝  ╚═════╝ ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝

[/bold cyan]
"""

# ── 超窄版 Logo ───────────────────────────────────────────

PIXEL_LOGO_TINY = """
[bold cyan]
╔═══════════════════════════════════╗
║      M  O  O  D  L  O  G          ║
╚═══════════════════════════════════╝
[/bold cyan]
"""

# ── 情绪主题渐变条 ─────────────────────────────────────────

MOOD_GRADIENT = (
    "[red]█[/red][orange3]█[/orange3][yellow]█[/yellow]"
    "[green]█[/green][cyan]█[/cyan][blue]█[/blue][magenta]█[/magenta]"
)


# ── 心情符号进度动画帧 ─────────────────────────────────────

MOOD_PROGRESS_FRAMES = [
    "     ",
    "  📝  ",
    "  📝 💭  ",
    "  📝 💭 📔  ",
    "  📝 💭 📔 ✨  ",
]


# ── 分数选择时的 ASCII 装饰线 ───────────────────────────────

SCORE_BORDER = {
    1: ("🔴", "red", "─── ▼ ───"),
    2: ("🟠", "dark_orange", "─── ▼ ───"),
    3: ("🟡", "yellow", "─── ▼ ───"),
    4: ("🟢", "green", "─── ▼ ───"),
    5: ("✨", "bright_green", "─── ▼ ───"),
}


# ── 工具函数 ───────────────────────────────────────────────

def _get_terminal_width() -> int:
    """获取终端宽度。"""
    try:
        return console.size.width
    except Exception:
        return 80


def _select_logo() -> str:
    """根据终端宽度选择合适的 Logo。"""
    width = _get_terminal_width()
    if width >= 70:
        return PIXEL_LOGO
    elif width >= 55:
        return PIXEL_LOGO_COMPACT
    else:
        return PIXEL_LOGO_TINY


def _sleep(seconds: float) -> None:
    """睡眠指定秒数。"""
    time.sleep(seconds)


# ── 动画效果函数 ───────────────────────────────────────────

def _loading_bar(
    prefix: str = "Loading",
    width: int = 35,
    delay: float = 0.025,
) -> None:
    """
    平滑加载条动画。
    """
    for i in range(width + 1):
        filled = "█" * i
        empty = "░" * (width - i)
        percent = int(i / width * 100)
        line = f"  {prefix}  {filled}{empty} {percent:3d}%"
        print(line, end="\r", flush=True)
        _sleep(delay)
    
    print()


# ── 新版出场动画 ───────────────────────────────────────────

def animate_splash(console_obj: Console | None = None) -> None:
    """
    出场动画：复古像素风 + 现代动画
    保留 Claude Code 风格的大号像素字母
    """
    c = console_obj or console

    # 阶段 1：清屏 + Logo 显示
    c.clear()
    c.print()
    c.print(_select_logo())
    _sleep(0.2)

    # 阶段 2：情绪渐变条
    c.print()
    gradient = MOOD_GRADIENT * 6
    c.print(f"[dim]{gradient[:60]}[/dim]")
    _sleep(0.15)

    # 阶段 3：版本信息
    c.print()
    from moodlog import __version__
    c.print(f"  [bold white]MoodLog v{__version__}[/bold white]")
    c.print("  [dim]Terminal Mood Diary · Minimalist & Powerful[/dim]")
    _sleep(0.2)

    # 阶段 4：加载条
    c.print()
    _loading_bar(prefix="Loading", width=35, delay=0.025)
    _sleep(0.1)

    # 阶段 5：快捷命令
    c.print()
    c.print("  [bold]Quick Commands[/bold]")
    c.print()

    commands = [
        ("record", "记录心情"),
        ("today", "今日回顾"),
        ("trend", "趋势分析"),
        ("stats", "统计面板"),
        ("view", "历史日记"),
    ]

    for cmd, desc in commands:
        c.print(f"  [cyan]moodlog {cmd}[/cyan]  [dim]→[/dim]  {desc}")

    # 阶段 6：结束
    c.print()
    c.print(f"  [dim]{MOOD_GRADIENT * 4}[/dim]")
    c.print()
    c.print("  [dim]Tip: moodlog --help 查看所有命令[/dim]")
    c.print()


# ── 保持向后兼容 ────────────────────────────────────────────

def animate_logo(console: Console | None = None, fps: float = 0.35) -> None:
    """Logo 动画（保持向后兼容）。"""
    c = console or Console()
    c.print(PIXEL_LOGO)
    c.print()


def animate_loading(
    text: str = "正在加载",
    duration: float = 1.2,
    console: Console | None = None,
) -> None:
    """带心情符号轮播的"加载"动画。"""
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
    """记录成功后的"心情闪光"效果。"""
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
        c.print("\033[F" * 1, end="")
    c.print(f"[bold {color}]  ✨ 记录成功！{emoji}  [/bold {color}]")


def score_picker_visual(console: Console | None = None) -> int:
    """可视化分数选择菜单。"""
    from rich.prompt import Prompt

    c = console or Console()
    c.print()
    c.print("[bold cyan]╭─────────────────────────────────╮[/bold cyan]")
    c.print("[bold cyan]│       请选择今天的心情        │[/bold cyan]")
    c.print("[bold cyan]╰─────────────────────────────────╯[/bold cyan]")
    c.print()

    options = [
        ("1", "😔", "很低  —  今天很难", "red", "██░░░"),
        ("2", "😕", "偏低  —  有点低落", "dark_orange", "████░░░░░"),
        ("3", "😐", "一般  —  平平淡淡", "yellow", "██████░░░░"),
        ("4", "🙂", "不错  —  感觉挺好", "green", "████████░░"),
        ("5", "😄", "很棒  —  超级开心", "bright_green", "██████████"),
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
    """让一段文字在彩色边框内"脉冲"闪烁。"""
    c = console or Console()
    for _ in range(repeat):
        c.print(f"[{color}]{text}[/{color}]")
        time.sleep(0.25)
        c.print("[dim]" + text + "[/dim]")
        time.sleep(0.25)


def _random_flourish() -> str:
    """返回随机心情装饰线。"""
    return random.choice([
        "✨ 📔 ✨",
        "💭 ── 💭",
        "📝 ~ ☁️ ~ 📝",
        "─═─ 📔 ─═─",
        "· · · ◆ · · ·",
    ])


def splash_screen(console: Console | None = None) -> None:
    """完整出场画面。"""
    c = console or Console()
    animate_splash(c)


# ── 旧版 Logo 帧数据（保持向后兼容）─────────────────────────

LOGO_FRAMES = [
    r"""[dim]
     ╭─────────────────────────────────╮
     │                                 │
     │                                 │
     │                                 │
     │                                 │
     │                                 │
     ╰─────────────────────────────────╯
    [/dim]""",
    r"""[dim cyan]
     ╭─────────────────────────────────╮
     │  · · · · · · · · · · · · · ·  │
     │                                 │
     │                                 │
     │  · · · · · · · · · · · · · ·  │
     │                                 │
     ╰─────────────────────────────────╯
    [/dim cyan]""",
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
