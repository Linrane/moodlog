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
@click.argument("score", type=click.IntRange(1, 5), required=False)
@click.option("-n", "--note", default="", help="日记内容（引号包裹）")
@click.option("-t", "--tag", "tags", multiple=True, help="标签（可多次使用：-t 工作 -t 运动）")
@click.option("-d", "--date", "record_date", default=None, help="记录日期（默认今天），格式 YYYY-MM-DD")
@click.option("--force", is_flag=True, default=False, help="已有记录时直接覆盖，不询问")
def record_cmd(score, note, tags, record_date, force):
    """📝 记录心情（评分 1-5）。

    \b
    示例：
      moodlog record 4
      moodlog record 4 -n "今天完成了项目" -t 工作 -t 编程
      moodlog record 3 -d 2026-05-08
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
