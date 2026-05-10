"""
MoodLog - config.py
读取 TOML 配置文件，提供全局配置访问接口。
优先级：环境变量 > config.toml > 内置默认值

v3: 增加 language 字段，支持 i18n 多语言切换。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Python 3.11+ 标准库内置 tomllib；3.10 需要 tomllib 第三方包
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib  # type: ignore[no-redef]
    except ImportError:
        import tomllib  # type: ignore[no-redef]  # noqa: F811

# ── 路径常量 ────────────────────────────────────────────────────
# 项目根目录（pyproject.toml 所在处）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_FILE = Path(__file__).resolve().parent / "config.toml"
_CONFIG_EXAMPLE = Path(__file__).resolve().parent / "config.toml.example"
_DEFAULT_DB_PATH = _PROJECT_ROOT / "data" / "moodlog.db"

# ── 默认配置 ────────────────────────────────────────────────────
_DEFAULTS: dict = {
    "database": {
        "path": str(_DEFAULT_DB_PATH),
    },
    "ui": {
        "mood_emoji": ["😫", "😔", "😐", "😊", "🤩", "🚀"],
        "mood_labels": ["很差", "较差", "一般", "不错", "很棒", "宇宙无敌爆炸开心"],
        "default_trend_days": 7,
    },
    "reminder": {
        "enabled": False,
        "time": "21:00",
    },
    "language": "zh_CN",
}


def _load_toml() -> dict:
    """加载 TOML 配置，不存在则复制 example 并返回默认值。"""
    if not _CONFIG_FILE.exists():
        if _CONFIG_EXAMPLE.exists():
            import shutil
            shutil.copy(_CONFIG_EXAMPLE, _CONFIG_FILE)
        return {}
    with open(_CONFIG_FILE, "rb") as f:
        return tomllib.load(f)


def _deep_merge(base: dict, override: dict) -> dict:
    """递归合并两个字典，override 优先。"""
    result = base.copy()
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


class Config:
    """全局配置单例。"""

    _instance: Config | None = None
    _data: dict

    def __new__(cls) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        toml_data = _load_toml()
        self._data = _deep_merge(_DEFAULTS, toml_data)
        # 环境变量覆盖
        if db_path := os.environ.get("MOODLOG_DB_PATH"):
            self._data["database"]["path"] = db_path

    # ── 便捷属性 ─────────────────────────────────────────────────
    @property
    def db_path(self) -> Path:
        p = Path(self._data["database"]["path"])
        if not p.is_absolute():
            p = (_PROJECT_ROOT / p).resolve()
        return p

    @property
    def mood_emoji(self) -> list[str]:
        return self._data["ui"]["mood_emoji"]

    @property
    def mood_labels(self) -> list[str]:
        return self._data["ui"]["mood_labels"]

    @property
    def default_trend_days(self) -> int:
        return int(self._data["ui"]["default_trend_days"])

    @property
    def reminder_enabled(self) -> bool:
        return bool(self._data["reminder"]["enabled"])

    @property
    def reminder_time(self) -> str:
        return self._data["reminder"]["time"]

    @property
    def language(self) -> str:
        """当前语言代码，如 'zh_CN'、'en_US'。"""
        return self._data.get("language", "zh_CN")

    def mood_display(self, score: int) -> str:
        """返回 '4⭐ 不错' 格式的心情显示文本（i18n-aware）。
        
        特殊处理：
          - score == 100: 宇宙无敌爆炸开心（彩蛋）
          - 其他: 正常 1-5 分逻辑
        """
        # 彩蛋：100分
        if score == 100:
            return "100⭐ 🚀 宇宙无敌爆炸开心"
        
        idx = max(0, min(4, score - 1))
        emoji = self.mood_emoji[idx]
        # 非中文模式下，从 i18n 加载翻译后的标签
        if self.language != "zh_CN":
            i18n = __import__("moodlog.utils.i18n", fromlist=["mood_label"]).i18n
            label = i18n.mood_label(score)
        else:
            label = self.mood_labels[idx]
        return f"{score}⭐ {emoji} {label}"

    # 允许在测试中重置单例
    @classmethod
    def reset(cls) -> None:
        cls._instance = None


# 模块级便捷访问
config = Config()
