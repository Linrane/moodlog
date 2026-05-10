"""
MoodLog - main.py
Click 命令行入口，注册所有子命令。
"""
from __future__ import annotations

import click
from rich.console import Console

from . import __version__
from .utils.art import splash_screen, PIXEL_LOGO, PIXEL_LOGO_COMPACT, PIXEL_LOGO_TINY
from .commands import (
    record_cmd, today_cmd, view_cmd,
    trend_cmd, stats_cmd, export_cmd, remind_cmd, report_cmd,
)

console = Console()

BANNER = """[bold cyan]
 __  __                 _ _               
|  \\/  | ___   ___   __| | |    ___   __ _ 
| |\\/| |/ _ \\ / _ \\ / _` | |   / _ \\ / _` |
| |  | | (_) | (_) | (_| | |__| (_) | (_| |
|_|  |_|\\___/ \\___/ \\__,_|_____\\___/ \\__, |
                                      |___/ 
[/bold cyan][dim]终端心情日记 · 极简记录，丰富回顾[/dim]
"""


@click.group(invoke_without_command=True, 
            epilog="""
\b
快速开始：
  moodlog record 4          快速记录心情（评分 1-5）
  moodlog record            进入交互式记录
  moodlog today             查看今天的心情
  moodlog trend             查看近 7 天趋势图
  moodlog stats             查看统计面板

\b
命令分类：
  📝 记录           record, today
  🔍 查看           view, trend, stats
  📤 导出           export, report
  ⚙️  管理           remind

\b
常用示例：
  moodlog record 5 -n "今天超级开心！" -t 生活
  moodlog view --last 30
  moodlog stats -c
  moodlog export -f markdown -o ~/diary.md

\b
更多信息：
  配置文件: ~/.moodlog/config.json
  数据库:   ~/.moodlog/moodlog.db
  文档:     https://github.com/Linrane/MoodLog

运行 'moodlog COMMAND --help' 查看子命令详情。
""")
@click.version_option(version=__version__, prog_name="MoodLog",
                    message="%(prog)s version %(version)s")
@click.pass_context
def cli(ctx):
    """
    📔 MoodLog v{version} - 终端心情日记

    极简记录，丰富回顾。让数据帮你看见情绪的变化。
    """.format(version=__version__)
    if ctx.invoked_subcommand is None:
        splash_screen(console)
        click.echo(ctx.get_help())


# 注册所有命令
cli.add_command(record_cmd, name="record")
cli.add_command(today_cmd, name="today")
cli.add_command(view_cmd, name="view")
cli.add_command(trend_cmd, name="trend")
cli.add_command(stats_cmd, name="stats")
cli.add_command(export_cmd, name="export")
cli.add_command(remind_cmd, name="remind")
cli.add_command(report_cmd, name="report")


# 支持 `python -m moodlog` 方式运行
if __name__ == "__main__":
    cli()
