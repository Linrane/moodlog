"""
MoodLog - commands/delete.py
删除指定日期的心情记录。
"""
from __future__ import annotations

import click

from ..database import get_mood_by_date, delete_mood, init_db
from ..utils.display import (
    console, print_success, print_warning, print_error,
)
from ..config import config


@click.command("delete")
@click.argument("date_str", required=False)
@click.option("-d", "--date", "record_date", default=None,
              help="要删除的日期（YYYY-MM-DD），默认今天")
@click.option("--force", is_flag=True, default=False,
              help="直接删除，无需确认")
def delete_cmd(date_str, record_date, force):
    """🗑️ 删除指定日期的心情记录。

    删除后会同时清理该记录关联的所有标签。

    \b
    示例：
      moodlog delete                   # 删除今天的记录
      moodlog delete 2026-05-08      # 删除指定日期
      moodlog delete -d 2026-05-08    # 同上
      moodlog delete --force          # 不询问直接删除今天

    \b
    提示：
      - 删除操作不可恢复，请确认后再操作
      - 如需修改记录，使用 moodlog record --force 更方便
    """
    init_db()

    # 确定要删除的日期
    from datetime import date as date_cls
    if date_str:
        try:
            target = date_cls.fromisoformat(date_str)
        except ValueError:
            print_error("日期格式不对哦 😅  应该是 YYYY-MM-DD，例如 2026-05-11")
            return
    elif record_date:
        try:
            target = date_cls.fromisoformat(record_date)
        except ValueError:
            print_error("日期格式不对哦 😅  应该是 YYYY-MM-DD，例如 2026-05-11")
            return
    else:
        target = date_cls.today()

    # 检查是否存在
    existing = get_mood_by_date(target)
    if existing is None:
        print_warning(f"{target} 还没有记录哦 📭  不需要删除~")
        return

    # 显示待删除内容
    console.print()
    display_score = config.mood_display(existing.mood_score)
    if existing.note:
        preview = existing.note[:30] + ("…" if len(existing.note) > 30 else "")
    else:
        preview = "（无日记）"
    console.print(f"[dim]  📅 {target}[/dim]")
    console.print(f"[dim]  {display_score}[/dim]")
    console.print(f"[dim]  📝 {preview}[/dim]")
    console.print()

    # 确认删除
    if not force:
        if not click.confirm(f"确定要删除 {target} 的记录吗？这不可撤销哦 🗑️"):
            print_warning("算了，不删了 👋")
            return

    # 执行删除
    success = delete_mood(target)
    if success:
        print_success(f"{target} 的记录已删除 🎯")
    else:
        print_error(f"删除失败了，请重试 😅")
