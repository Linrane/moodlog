"""
MoodLog - utils/report.py
使用 matplotlib 生成月度情绪报告图片。
轻量化实现，中文显示适配。
"""

from __future__ import annotations

import warnings
warnings.filterwarnings("ignore")

import os
from datetime import date, timedelta
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.font_manager import FontManager, FontProperties

from ..config import config
from ..database import get_moods_by_range, init_db

# 强制使用非交互后端，不需要显示器
matplotlib.use("Agg")

# ── 中文字体自动检测 ────────────────────────────────────────────
_FONT_CACHE = None


def _get_chinese_font() -> str | None:
    """自动检测系统中可用的中文字体路径，缓存结果。"""
    import sys, os
    global _FONT_CACHE
    if _FONT_CACHE is not None:
        return _FONT_CACHE

    fm = FontManager()
    preferred = [
        "SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei",
        "Noto Sans CJK SC", "Source Han Sans SC",
        "PingFang SC", "STHeiti", "Arial Unicode MS",
    ]
    available = {f.name for f in fm.ttflist}
    for name in preferred:
        if name in available:
            for f in fm.ttflist:
                if f.name == name:
                    _FONT_CACHE = f.fname
                    return _FONT_CACHE

    # Windows：直接检查常见字体文件路径
    if sys.platform == "win32":
        win_paths = [
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\simsun.ttc",
            r"C:\Windows\Fonts\msyhbd.ttc",
            r"C:\Windows\Fonts\STHeiti.ttf",
        ]
        for p in win_paths:
            if os.path.exists(p):
                _FONT_CACHE = p
                return _FONT_CACHE

    # 回退：找包含 CJK 或 Chinese 的字体
    for f in fm.ttflist:
        if any(kw in f.name.lower() for kw in ["cjk", "chinese", "noto", "hei", "song"]):
            _FONT_CACHE = f.fname
            return _FONT_CACHE

    _FONT_CACHE = None
    return None


def _configure_font(ax: plt.Axes | None = None) -> str | None:
    """配置中文字体，返回可用的字体路径（用于后续显式传 fontproperties）。"""
    font_path = _get_chinese_font()
    if font_path:
        import matplotlib.font_manager as fm
        fm.fontManager.addfont(font_path)
        prop = fm.FontProperties(fname=font_path)
        matplotlib.rcParams["font.family"] = prop.get_name()
        matplotlib.rcParams["axes.unicode_minus"] = False
        return font_path
    else:
        matplotlib.rcParams["axes.unicode_minus"] = False
        return None


# ── 颜色映射 ─────────────────────────────────────────────────────
SCORE_COLOR_HEX = {
    1: "#E74C3C",   # 红
    2: "#E67E22",   # 暗橙
    3: "#F1C40F",   # 黄
    4: "#2ECC71",   # 绿
    5: "#1ABC9C",   # 青绿
    100: "#FF00FF", # 彩蛋：亮洋红
}


def generate_monthly_report(
    year: int | None = None,
    month: int | None = None,
    output_path: str | None = None,
) -> str:
    """
    生成指定月份的的情绪报告 PNG 图片。
    返回生成的文件路径。

    参数：
      year, month：不传则默认当月
      output_path：输出路径，不传则自动生成到 ~/moodlog_reports/
    """
    init_db()
    today = date.today()
    y = year or today.year
    m = month or today.month

    # 计算月份起止
    start = date(y, m, 1)
    if m == 12:
        end = date(y + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(y, m + 1, 1) - timedelta(days=1)

    entries = get_moods_by_range(start, end)
    all_dates = [start + timedelta(days=i) for i in range((end - start).days + 1)]

    # 构建每日分数数组（无记录为 None）
    entry_map = {e.date: e for e in entries}
    scores = [entry_map[d].mood_score if d in entry_map else None for d in all_dates]

    # ── 绘图 ──────────────────────────────────────────────────────
    font_path = _configure_font()
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), constrained_layout=True)
    fig.patch.set_facecolor("#1a1a2e")

    # 子图 1：日历热力图
    _draw_calendar_heatmap(ax=axes[0], year=y, month=m, entry_map=entry_map,
                           all_dates=all_dates, scores=scores, font_path=font_path)

    # 子图 2：趋势折线图
    _draw_trend_line(ax=axes[1], all_dates=all_dates, scores=scores, year=y, month=m,
                     font_path=font_path)

    # 总体标题
    fp_main = FontProperties(fname=font_path) if font_path else None
    fig.suptitle(f"MoodLog · {y}年{m}月情绪报告",
                 fontsize=16, fontweight="bold", color="white",
                 fontproperties=fp_main)

    # 保存
    if output_path is None:
        out_dir = Path.home() / "moodlog_reports"
        out_dir.mkdir(exist_ok=True)
        output_path = str(out_dir / f"moodlog_{y:04d}_{m:02d}.png")

    fig.savefig(output_path, dpi=150, bbox_inches="tight",
               facecolor=fig.get_facecolor())
    plt.close(fig)
    return output_path


def _draw_calendar_heatmap(ax, year, month, entry_map, all_dates, scores,
                            font_path=None):
    """绘制月历热力图。"""
    import calendar as cal_mod
    from matplotlib.font_manager import FontProperties

    ax.set_facecolor("#16213e")
    ax.set_xlim(-0.5, 6.5)
    ax.set_ylim(6.5, -0.5)

    weeks = cal_mod.monthcalendar(year, month)

    date_to_pos = {}
    for week_idx, week in enumerate(weeks):
        for day_idx, day in enumerate(week):
            if day != 0:
                d = date(year, month, day)
                date_to_pos[d] = (week_idx, day_idx)

    fp = FontProperties(fname=font_path) if font_path else None

    for d, (w, wd) in date_to_pos.items():
        entry = entry_map.get(d)
        if entry:
            color = SCORE_COLOR_HEX.get(entry.mood_score, "#555555")
            rect = mpatches.FancyBboxPatch(
                (wd - 0.4, w + 0.1), 0.8, 0.8,
                boxstyle="round,pad=0.05",
                facecolor=color, edgecolor="white", linewidth=0.5, alpha=0.85
            )
            ax.add_patch(rect)
            ax.text(wd, w + 0.5, str(d.day), ha="center", va="center",
                    fontsize=12, color="white", fontweight="bold",
                    fontproperties=fp)
            # 100分彩蛋：安全访问，兼容越界
            if entry.mood_score == 100:
                label = "🚀宇宙无敌开心"
            else:
                label = config.mood_labels[entry.mood_score - 1]
            ax.text(wd, w + 0.18, label, ha="center", va="center",
                    fontsize=8, color="white", alpha=0.9,
                    fontproperties=fp)
        else:
            if d > date.today():
                text_color = "#444444"
            else:
                text_color = "#666666"
            ax.text(wd, w + 0.5, str(d.day), ha="center", va="center",
                    fontsize=10, color=text_color, fontproperties=fp)

    weekdays = ["一", "二", "三", "四", "五", "六", "日"]
    for i, name in enumerate(weekdays):
        ax.text(i, -0.3, name, ha="center", va="bottom",
                fontsize=11, color="#AAAAAA", fontweight="bold",
                fontproperties=fp)

    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(f"{year}年{month}月", color="white", fontsize=12, pad=10,
                 fontproperties=fp)

    # 图例
    handles = [
        mpatches.Patch(color=SCORE_COLOR_HEX[i],
                        label=f"{i}分 {config.mood_labels[i-1]}")
        for i in range(1, 6)
    ]
    # 100分彩蛋专属图例项
    handles.append(mpatches.Patch(
        color=SCORE_COLOR_HEX[100],
        label="100分 🚀 宇宙无敌开心"
    ))
    ax.legend(handles=handles, bbox_to_anchor=(1.01, 1), loc="upper left",
              fontsize=8, facecolor="#1a1a2e", edgecolor="#444444",
              labelcolor="white", prop=fp)


def _draw_trend_line(ax, all_dates, scores, year, month, font_path=None):
    """绘制月度趋势折线图。"""
    from matplotlib.font_manager import FontProperties

    ax.set_facecolor("#16213e")
    ax.spines["bottom"].set_color("#444444")
    ax.spines["left"].set_color("#444444")
    ax.tick_params(colors="white", labelsize=9)
    ax.yaxis.grid(True, color="#333333", linewidth=0.5)
    ax.set_ylim(0.5, 5.5)
    ax.set_yticks([1, 2, 3, 4, 5])
    # Y 轴用文字标签，不用 emoji（字体不一定支持）
    fp = FontProperties(fname=font_path) if font_path else None
    labels = ax.set_yticklabels(
        [f"{i}  {config.mood_labels[i - 1]}" for i in range(1, 6)],
        fontsize=9, fontproperties=fp
    )
    # 给每个 Y 轴标签上色
    for tick, score in zip(ax.get_yticklabels(), range(1, 6)):
        tick.set_color(SCORE_COLOR_HEX[score])

    # x 轴：每隔 5 天显示一个日期标签
    x_vals = list(range(len(all_dates)))
    ax.set_xticks(x_vals[::5])
    ax.set_xticklabels([str(d.day) for d in all_dates[::5]],
                       color="#AAAAAA", fontsize=8, fontproperties=fp)
    ax.set_xlabel("日期（日）", color="white", fontsize=10,
                  fontproperties=fp)

    # 折线：只连有记录的日期，100分截断为5避免越界
    plot_dates, plot_scores = [], []
    for d, s in zip(all_dates, scores):
        if s is not None:
            plot_dates.append(d)
            plot_scores.append(min(s, 5))  # 100分在图上截断为5

    if plot_scores:
        x_indices = [all_dates.index(d) for d in plot_dates]
        ax.plot(x_indices, plot_scores, color="#00d2ff", linewidth=2.5,
                marker="o", markersize=6, markerfacecolor="#00d2ff",
                markeredgecolor="white", markeredgewidth=1, alpha=0.9)

        # 平均分参考线（排除100分彩蛋）
        valid = [s for s in plot_scores if s != 100]
        avg = sum(valid) / len(valid) if valid else 0
        ax.axhline(avg, color="#FF6B6B", linewidth=1.2, linestyle="--",
                   alpha=0.7, label=f"均值 {avg:.1f}")
        ax.legend(facecolor="#1a1a2e", edgecolor="#444444",
                  labelcolor="white", fontsize=8, prop=fp)

    ax.set_title("情绪趋势", color="white", fontsize=12, pad=10,
                 fontproperties=fp)
