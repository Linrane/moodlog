"""
MoodLog - commands/export.py
将日记导出为 Markdown / JSON / CSV 格式。
v2：接入 i18n。
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import date
from io import StringIO
from pathlib import Path

import click

from ..database import get_all_moods, get_moods_by_range, init_db
from ..config import config
from ..utils.display import print_success, print_warning, print_error, console
from ..utils.i18n import t


def _mood_label_safe(score: int) -> str:
    """安全获取情绪标签，兼容100分彩蛋。"""
    if score == 100:
        return "宇宙无敌爆炸开心"
    idx = max(0, min(4, score - 1))
    return config.mood_labels[idx]


def _to_markdown(entries) -> str:
    lines = ["# MoodLog 心情日记导出\n"]
    for e in entries:
        mood_str = config.mood_display(e.mood_score)
        tags_str = " ".join(f"#{tg}" for tg in e.tags)
        lines.append(f"## {e.date}  {mood_str}")
        if tags_str:
            lines.append(f"\n**标签**：{tags_str}")
        if e.note:
            lines.append(f"\n{e.note}")
        lines.append("\n---\n")
    return "\n".join(lines)


def _to_json(entries) -> str:
    data = [
        {
            "date": str(e.date),
            "mood_score": e.mood_score,
            "mood_label": _mood_label_safe(e.mood_score),
            "note": e.note,
            "tags": e.tags,
            "created_at": e.created_at.isoformat(),
            "updated_at": e.updated_at.isoformat(),
        }
        for e in entries
    ]
    return json.dumps(data, ensure_ascii=False, indent=2)


def _to_csv(entries) -> str:
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "mood_score", "mood_label", "note", "tags", "created_at"])
    for e in entries:
        writer.writerow([
            str(e.date),
            e.mood_score,
            _mood_label_safe(e.mood_score),
            e.note,
            "|".join(e.tags),
            e.created_at.isoformat(),
        ])
    return buf.getvalue()


@click.command("export")
@click.option(
    "--format", "-f", "fmt",
    type=click.Choice(["markdown", "json", "csv"], case_sensitive=False),
    default="markdown",
    show_default=True,
    help="导出格式：markdown（易读）、json（程序处理）、csv（表格）",
)
@click.option("--output", "-o", default=None, 
              help="输出文件路径（默认打印到终端）")
@click.option("--from", "date_from", default=None, 
              help="开始日期（YYYY-MM-DD）")
@click.option("--to", "date_to", default=None, 
              help="结束日期（YYYY-MM-DD）")
def export_cmd(fmt, output, date_from, date_to):
    """📤 导出日记数据。

    支持三种格式导出：
      - markdown：易读的文本格式，适合打印或分享
      - json：结构化数据，适合程序处理
      - csv：表格格式，适合 Excel 打开

    \b
    示例：
      moodlog export                        # 导出所有数据为 Markdown（打印到终端）
      moodlog export -f json                # 导出为 JSON 格式
      moodlog export -f csv -o data.csv     # 导出为 CSV 文件
      moodlog export -o diary.md            # 导出到指定文件
      moodlog export --from 2026-01-01 --to 2026-12-31  # 导出指定范围

    \b
    提示：
      - 不指定 --output 时，内容会打印到终端
      - CSV 格式中标签用 "|" 分隔
      - JSON 格式包含所有字段（日期、评分、标签、备注等）
    """
    init_db()

    # 获取数据
    if date_from or date_to:
        try:
            start = date.fromisoformat(date_from) if date_from else date(2000, 1, 1)
            end = date.fromisoformat(date_to) if date_to else date.today()
        except ValueError as e:
            print_error(t("record.messages.date_format_error", date=str(e)))
            sys.exit(1)
        entries = get_moods_by_range(start, end)
    else:
        entries = get_all_moods()

    if not entries:
        print_warning(t("export.none"))
        return

    # 格式化
    fmt_lower = fmt.lower()
    if fmt_lower == "markdown":
        content = _to_markdown(entries)
    elif fmt_lower == "json":
        content = _to_json(entries)
    else:
        content = _to_csv(entries)

    # 输出
    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        print_success(t("export.success", path=out_path.resolve()))
    else:
        console.print(content)
        console.print(f"[dim]{t('export.printed')}[/dim]")
