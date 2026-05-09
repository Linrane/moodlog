"""
MoodLog - utils/notify.py
跨平台桌面通知封装（依赖 plyer）。
"""
from __future__ import annotations


def send_notification(title: str = "MoodLog 提醒", message: str = "别忘了记录今天的心情 😊") -> bool:
    """
    发送桌面通知。
    成功返回 True，不支持或失败返回 False（不抛出异常，降级静默处理）。
    """
    try:
        from plyer import notification  # type: ignore
        notification.notify(
            title=title,
            message=message,
            app_name="MoodLog",
            timeout=8,
        )
        return True
    except Exception:
        return False
