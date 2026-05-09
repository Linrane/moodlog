"""
MoodLog - commands/remind.py
管理每日提醒（Windows 计划任务 / macOS/Linux crontab）。
v2：接入 i18n。
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console

from ..config import config
from ..utils.display import print_error, print_success, print_warning, console
from ..utils.i18n import t

_IS_WINDOWS = os.name == "nt"
_TASK_NAME = "MoodLog_DailyReminder"


def _get_moodlog_exe() -> str | None:
    """获取 moodlog 可执行文件路径。"""
    return shutil.which("moodlog")


@click.group("remind")
def remind_cmd():
    """⏰ 管理每日提醒。"""


@remind_cmd.command("on")
@click.option("--time", "-t", "remind_time", default=None,
              help="提醒时间（HH:MM），默认使用配置文件中的时间")
def remind_on(remind_time):
    """开启每日记录提醒。"""
    from ..utils import art
    t_str = remind_time or config.reminder_time
    try:
        parts = t_str.split(":")
        assert 0 <= int(parts[0]) <= 23
        assert 0 <= int(parts[1]) <= 59
    except Exception:
        print_error(t("remind.invalid_time", time=t_str))
        return

    if _IS_WINDOWS:
        exe = _get_moodlog_exe()
        if not exe:
            print_error(t("remind.moodlog_not_found"))
            return
        cmd = (
            f'schtasks /Create /SC DAILY /TN "{_TASK_NAME}" '
            f'/TR "{exe} today" /ST {t_str} /F'
        )
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print_success(t("remind.enabled"))
        else:
            print_error(t("remind.enable_failed"))
            if result.stderr:
                console.print(f"[dim]{result.stderr}[/dim]")
    else:
        exe = _get_moodlog_exe() or "moodlog"
        entry = f"{t_str.split(':')[0]} {t_str.split(':')[1]} * * * {exe} today"
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        lines = [l for l in result.stdout.splitlines() if "moodlog" not in l.lower()]
        lines.append(entry)
        proc = subprocess.run(["crontab", "-"], input="\n".join(lines),
                             capture_output=True, text=True)
        if proc.returncode == 0:
            print_success(t("remind.enabled"))
        else:
            print_error(t("remind.enable_failed"))


@remind_cmd.command("off")
def remind_off():
    """关闭每日记录提醒。"""
    if _IS_WINDOWS:
        result = subprocess.run(
            f'schtasks /Delete /TN "{_TASK_NAME}" /F',
            capture_output=True, text=True, shell=True,
        )
        if result.returncode == 0:
            print_success(t("remind.disabled"))
        else:
            print_warning(t("remind.not_found"))
    else:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        lines = [l for l in result.stdout.splitlines() if "moodlog" not in l.lower()]
        proc = subprocess.run(["crontab", "-"], input="\n".join(lines),
                             capture_output=True, text=True)
        if proc.returncode == 0:
            print_success(t("remind.disabled"))
        else:
            print_warning(t("remind.not_found"))


@remind_cmd.command("status")
def remind_status():
    """查看提醒状态。"""
    if _IS_WINDOWS:
        result = subprocess.run(
            f'schtasks /Query /TN "{_TASK_NAME}"',
            capture_output=True, text=True, shell=True,
        )
        if result.returncode == 0:
            print_success(t("remind.status_on"))
            console.print(result.stdout, style="dim")
        else:
            print_warning(t("remind.status_off"))
    else:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        found = any("moodlog" in l.lower() for l in result.stdout.splitlines())
        if found:
            print_success(t("remind.status_on"))
            for line in result.stdout.splitlines():
                if "moodlog" in line.lower():
                    console.print(line, style="dim")
        else:
            print_warning(t("remind.status_off"))
