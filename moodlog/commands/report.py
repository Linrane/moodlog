"""
MoodLog - commands/report.py
生成月度情绪报告 PNG 图片。
v2：接入 i18n。
"""

from __future__ import annotations

from datetime import date

import click

from ..database import init_db
from ..utils.report import generate_monthly_report
from ..utils.display import (
    console, print_success, print_warning, print_error, print_info,
)
from ..utils.i18n import t


@click.command("report")
@click.option("--month", "-m", type=int, default=None,
              help="指定月份（1-12），默认当月")
@click.option("--year", "-y", type=int, default=None,
              help="指定年份，默认当年")
@click.option("--output", "-o", "output_path", default=None,
              help="输出图片路径（PNG），不指定则保存到 ~/moodlog_reports/")
def report_cmd(month, year, output_path):
    """🖼️ 生成月度情绪报告图片（PNG）。

    生成一张精美的情绪报告图片，包含：
      - 月度情绪概览
      - 每日情绪分布日历
      - 情绪趋势图表
      - 高频标签统计

    \b
    示例：
      moodlog report              # 生成当月的报告
      moodlog report -m 5         # 生成 5 月份的报告
      moodlog report -m 5 -y 2025  # 生成 2025 年 5 月的报告
      moodlog report -o report.png  # 指定输出文件路径

    \b
    提示：
      - 默认保存到 ~/moodlog_reports/ 目录
      - 生成的图片可以直接分享到社交媒体
      - 需要安装 Pillow 库：pip install Pillow
    """
    init_db()

    today = date.today()
    y = year or today.year
    m = month or today.month

    if not (1 <= m <= 12):
        print_error(t("errors.month_range"))
        return

    try:
        console.print(f"[dim]{t('report.generating')}...[/dim]")
        out = generate_monthly_report(year=y, month=m, output_path=output_path)
        print_success(t("report.success", path=out))
    except Exception as e:
        print_error(t("report.error", msg=str(e)))
        console.print_exception()
