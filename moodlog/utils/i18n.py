"""
MoodLog - utils/i18n.py
多语言支持（i18n）：JSON 翻译文件 + t() 函数。

设计原则：
- 默认语言：zh_CN（简体中文）
- 翻译文件：moodlog/locale/<lang>.json
- 运行时切换：config.language 字段
- t(key) 函数：key 不存在时回退到中文，再失败则返回 key 本身
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from ..config import config

# 线程局部存储，存放当前语言字典
_local = threading.local()

# 翻译文件目录
_LOCALE_DIR = Path(__file__).parent.parent / "locale"
_FALLBACK_LANG = "zh_CN"


def _load_locale(lang: str) -> dict[str, Any]:
    """加载指定语言的翻译文件，失败则返回空字典。"""
    path = _LOCALE_DIR / f"{lang}.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _get_active_lang() -> str:
    """返回当前配置的语言代码。"""
    return getattr(config, "language", _FALLBACK_LANG) or _FALLBACK_LANG


def _get_translations() -> dict[str, Any]:
    """获取当前线程的翻译字典（带缓存）。"""
    if not hasattr(_local, "translations"):
        lang = _get_active_lang()
        data = _load_locale(lang)
        # 如果当前语言不是中文，加载中文作为 fallback
        if lang != _FALLBACK_LANG:
            fallback = _load_locale(_FALLBACK_LANG)
            merged: dict[str, Any] = {}
            merged.update(fallback)
            _deep_update(merged, data)
            data = merged
        _local.translations = data
    return _local.translations


def _deep_update(base: dict, overrides: dict) -> None:
    """深度更新字典（递归合并嵌套 dict）。"""
    for k, v in overrides.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_update(base[k], v)
        else:
            base[k] = v


def t(key: str, default: str | None = None, **kwargs) -> str:
    """
    翻译函数。
    key 使用点分隔符，如 "record.prompt.score"
    支持格式化参数：t("stats.total_records", count=5)
    支持 default 参数：key 不存在时返回 default 值
    """
    translations = _get_translations()
    parts = key.split(".")
    node: Any = translations
    for p in parts:
        if isinstance(node, dict) and p in node:
            node = node[p]
        else:
            return default if default is not None else (key.format(**kwargs) if kwargs else key)
    if not isinstance(node, str):
        return str(node)
    return node.format(**kwargs) if kwargs else node


def reload_translations() -> None:
    """清除缓存，下次调用 t() 时重新加载。"""
    if hasattr(_local, "translations"):
        del _local.translations


# ── 情绪标签 / emoji 多语言辅助 ────────────────────────────────

def mood_label(score: int) -> str:
    """返回指定分数的情绪标签（当前语言）。兼容100分彩蛋。"""
    if score == 100:
        return "宇宙无敌爆炸开心"
    key = f"record.labels.{score}"
    result = t(key)
    if result == key:
        idx = max(0, min(4, score - 1))
        return config.mood_labels[idx]
    return result


def mood_emoji_char(score: int) -> str:
    """返回指定分数的 emoji 字符（当前语言，fallback 到 config）。兼容100分彩蛋。"""
    if score == 100:
        return "🚀"
    lang = _get_active_lang()
    if lang != _FALLBACK_LANG:
        translations = _get_translations()
        emojis = translations.get("record", {}).get("emoji", [])
        idx = max(0, min(4, score - 1))
        if emojis and len(emojis) > idx:
            return emojis[idx]
    emojis = config.mood_emoji
    if emojis and len(emojis) > max(0, min(4, score - 1)):
        return emojis[max(0, min(4, score - 1))]
    return "😐"


def mood_quote_i18n(score: int) -> str:
    """返回对应情绪的小结语（当前语言）。"""
    if score >= 4:
        key = "stats.mood_quote_high"
    elif score >= 3:
        key = "stats.mood_quote_mid"
    elif score >= 2:
        key = "stats.mood_quote_low"
    else:
        key = "stats.mood_quote_very_low"
    result = t(key)
    if result == key:
        from .display import _MOOD_QUOTES
        import random
        quotes = _MOOD_QUOTES.get(score, ["今天也辛苦了。"])
        return random.choice(quotes)
    return result
