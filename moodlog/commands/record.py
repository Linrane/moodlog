"""
MoodLog - commands/record.py
记录今日（或指定日期）心情的命令。
v2：接入 i18n，用户提示使用 t()。
"""
from __future__ import annotations

import sys
from datetime import date

import click
from rich.prompt import Confirm, Prompt

from ..config import config
from ..database import get_mood_by_date, insert_or_update_mood, init_db
from ..utils.display import (
    console, print_success, print_warning, print_error, print_info,
    score_text, mood_bar, entry_detail,
)
from ..utils.art import animate_mood_flash, score_picker_visual
from ..utils.i18n import t


@click.command("record")
@click.argument("score", type=click.INT, required=False)
@click.option("-n", "--note", default="", help="日记内容（支持中文，用引号包裹）")
@click.option("-t", "--tag", "tags", multiple=True, 
              help="标签（可多次使用：-t 工作 -t 编程；支持中文标签）")
@click.option("-d", "--date", "record_date", default=None, 
              help="记录日期（默认今天），格式 YYYY-MM-DD")
@click.option("--force", is_flag=True, default=False, 
              help="已有记录时直接覆盖，不询问")
def record_cmd(score, note, tags, record_date, force):
    """📝 记录心情（评分 1-5）。

    评分说明：
      1 = 😢 非常糟糕
      2 = 😕 不太好
      3 = 😐 一般般
      4 = 😊 不错
      5 = 🥰 超级棒
      100 = 🚀 宇宙无敌爆炸开心（彩蛋，仅支持命令行输入）

    \b
    示例：
      moodlog record 4                      # 快速记录评分 4
      moodlog record                         # 进入交互式记录
      moodlog record 5 -n "今天超级开心！"   # 带日记内容
      moodlog record 4 -n "完成了项目" -t 工作 -t 编程  # 带标签
      moodlog record 3 -d 2026-05-08        # 补记过去的日期
      moodlog record 4 --force               # 强制覆盖已有记录
      moodlog record 100                     # 彩蛋：宇宙无敌爆炸开心

    \b
    提示：
      - 不提供评分会进入交互式界面（带可视化评分选择器）
      - 不提供 -n 会在终端中提示输入
      - 标签可以帮助后续搜索和统计
      - 100 分是隐藏彩蛋，不会在交互式界面显示
    """
    init_db()

    # ── 解析日期 ────────────────────────────────────────────────
    if record_date:
        try:
            target_date = date.fromisoformat(record_date)
        except ValueError:
            print_error(t("record.messages.date_format_error", date=record_date))
            sys.exit(1)
    else:
        target_date = date.today()

    # ── 交互式输入评分（若未提供）────────────────────────────────
    if score is None:
        score = score_picker_visual(console)
    
    # ── 验证评分（1-5 或 100）────────────────────────────────────
    if score not in (1, 2, 3, 4, 5, 100):
        print_error(f"无效的评分：{score}。请输入 1-5 或 100（彩蛋）")
        sys.exit(1)

    # ── 检查是否已存在记录 ───────────────────────────────────────
    existing = get_mood_by_date(target_date)
    if existing and not force:
        print_warning(f"{target_date} 已有记录（{config.mood_display(existing.mood_score)}）。")
        if not Confirm.ask(t("record.prompt.confirm_overwrite"), default=False):
            print_info(t("record.messages.cancelled"))
            return

    # ── 交互式输入日记（若未通过 -n 提供）──────────────────────────
    if not note:
        note = Prompt.ask(
            f"[bold cyan]{t('record.prompt.note')}[/bold cyan]",
            default="",
        )

    # ── 写入 ─────────────────────────────────────────────────────
    entry, is_new = insert_or_update_mood(
        record_date=target_date,
        score=score,
        note=note.strip(),
        tags=list(tags),
    )

    # ── 输出确认 ─────────────────────────────────────────────────
    action_key = "record.messages.success_new" if is_new else "record.messages.success_update"
    console.print()
    console.print(entry_detail(entry))
    animate_mood_flash(score, console)
    print_success(t(action_key, date=target_date, display=config.mood_display(score)))
    console.print()


def print_info_neutral(msg: str) -> None:
    console.print(f"[dim]{msg}[/dim]")
