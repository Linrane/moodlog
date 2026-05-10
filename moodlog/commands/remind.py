"""
MoodLog - commands/remind.py
管理每日提醒（Windows 计划任务 / macOS/Linux crontab）。
v4：自动请求管理员权限创建计划任务。
"""
from __future__ import annotations

import os
import subprocess
import sys
import time

import click
from rich.console import Console

from ..config import config
from ..utils.display import print_error, print_success, print_warning, console
from ..utils.i18n import t

_IS_WINDOWS = os.name == "nt"
_TASK_NAME = "MoodLog_DailyReminder"


def _is_admin() -> bool:
    """检查当前是否有管理员权限。"""
    if not _IS_WINDOWS:
        return os.getuid() == 0
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def _run_as_admin(cmd: str) -> bool:
    """
    使用管理员权限运行命令（Windows）。
    通过 ShellExecuteW + 'runas' 触发 UAC 提权，
    并等待命令执行完毕，通过输出文件判断成功与否。
    """
    import ctypes, tempfile, os, time

    SW_HIDE = 0
    bat_file = tempfile.mktemp(suffix=".bat")
    out_file = bat_file + ".out"
    result = False

    try:
        with open(bat_file, "w", encoding="utf-8") as f:
            f.write(f'@echo off\r\n{cmd} > "{out_file}" 2>&1\r\n')

        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", "cmd.exe", f'/c "{bat_file}"', None, SW_HIDE
        )
        if ret <= 32:
            return False

        # 等待批处理执行完毕（输出文件出现即表示完成）
        for _ in range(80):
            if os.path.exists(out_file):
                break
            time.sleep(0.5)

        if os.path.exists(out_file):
            with open(out_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            # 中文系统 schtasks 成功时输出含"成功"，英文系统含"SUCCESS"
            result = "成功" in content or "SUCCESS" in content.upper()
        else:
            # 超时：可能用户拒绝了 UAC，按失败处理
            result = False
    except Exception:
        result = False
    finally:
        for p in (bat_file, out_file):
            try:
                if os.path.exists(p):
                    os.unlink(p)
            except Exception:
                pass

    return result


def _send_notification() -> None:
    """发送系统通知（使用 plyer）。"""
    try:
        from plyer import notification
        notification.notify(
            title="MoodLog 提醒",
            message="该记录今天的心情啦 🙂",
            app_name="MoodLog",
            timeout=10,
        )
    except Exception:
        pass


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
        py = sys.executable
        cmd = (
            f'schtasks /Create /SC DAILY /TN "{_TASK_NAME}" '
            f'/TR "\\"{py}\\" -m moodlog remind notify" '
            f'/ST {t_str} /F'
        )
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print_success(t("remind.enabled"))
            return

        # 权限不足且当前不是管理员 → 尝试自动提权
        err = result.stdout + result.stderr
        if ("拒绝访问" in err or "ERROR" in err.upper()) and not _is_admin():
            print_warning("权限不足，正在请求管理员提权（请允许 UAC 弹窗）…")
            if _run_as_admin(cmd):
                # 提权进程执行成功，二次确认任务已创建
                time.sleep(1)
                chk = subprocess.run(
                    f'schtasks /Query /TN "{_TASK_NAME}"',
                    capture_output=True, text=True, shell=True,
                )
                if chk.returncode == 0:
                    print_success(t("remind.enabled"))
                else:
                    print_error(t("remind.enable_failed"))
            else:
                print_error("UAC 提权失败，请手动以管理员身份运行终端后执行：moodlog remind on")
            return

        print_error(t("remind.enable_failed"))
        if result.stderr:
            console.print(f"[dim]{result.stderr}[/dim]")
    else:
        py = sys.executable
        entry = f'{t_str.split(":")[0]} {t_str.split(":")[1]} "{py}" -m moodlog remind notify'
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
        cmd = f'schtasks /Delete /TN "{_TASK_NAME}" /F'
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print_success(t("remind.disabled"))
            return

        err = result.stdout + result.stderr
        # 任务不存在 → 警告（不是错误）
        if "不存在" in err or "not exist" in err.lower() or "cannot find" in err.lower():
            print_warning(t("remind.not_found"))
            return

        # 权限不足且当前不是管理员 → 尝试提权
        if ("拒绝访问" in err or "ERROR" in err.upper()) and not _is_admin():
            print_warning("权限不足，正在请求管理员提权（请允许 UAC 弹窗）…")
            if _run_as_admin(cmd):
                time.sleep(1)
                chk = subprocess.run(
                    f'schtasks /Query /TN "{_TASK_NAME}"',
                    capture_output=True, text=True, shell=True,
                )
                if chk.returncode != 0:
                    print_success(t("remind.disabled"))
                else:
                    print_warning(t("remind.not_found"))
            else:
                print_error("UAC 提权失败，请手动以管理员身份运行终端后执行：moodlog remind off")
            return

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


@remind_cmd.command("notify")
def remind_notify():
    """发送 MoodLog 记录提醒通知（供计划任务调用）。"""
    _send_notification()
