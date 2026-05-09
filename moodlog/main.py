"""
MoodLog - main.py
Click 命令行入口，注册所有子命令。
"""
from __future__ import annotations

import click
from rich.console import Console

from .utils.art import splash_screen
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


@click.group(invoke_without_command=True)
@click.version_option(version="0.1.0", prog_name="MoodLog")
@click.pass_context
def cli(ctx):
    """
    MoodLog — 你的终端心情日记 📔

    \b
    快速开始：
      moodlog record 4          记录今天心情（快速）
      moodlog record            交互式记录
      moodlog today             查看今天的记录
      moodlog trend             查看近7天趋势
      moodlog stats             统计面板
    """
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
