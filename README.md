# MoodLog

> 终端心情日记。记录情绪，看见变化。

---

## 什么是 MoodLog

MoodLog 是一个运行在命令行里的心情记录工具。

每天用 1–5 分给当天打个分，可以附上一段日记或几个标签。积累一段时间后，用内置的统计、趋势图、月度报告来回顾：哪几天心情最好、哪些标签反复出现、最近的情绪走向是怎样的。

所有数据存在本地 SQLite 数据库里，不联网，不上传。数据库文件就在 `data/moodlog.db`，随时可以备份或迁移。

---

## 安装

```bash
# 克隆仓库
git clone https://github.com/Linrane/moodlog.git
cd moodlog

# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate     # Windows 用 .venv\Scripts\activate

# 安装
pip install -e ".[dev]"
```

安装完成后，在终端任意目录直接输入 `moodlog` 即可运行。首次启动会自动在 `moodlog/` 目录下生成配置文件 `config.toml`。

---

## 快速上手

记录今天的心情（直接给分，10 秒完成）：

```bash
moodlog record 4
```

带日记和标签：

```bash
moodlog record 4 -n "今天项目上线，一切顺利" -t 工作
```

不指定分数，进入交互式引导：

```bash
moodlog record
```

---

## 命令一览

### 记录

| 命令 | 说明 |
|------|------|
| `moodlog record [分数]` | 记录今日心情。分数 1–5，不填则进入交互模式 |
| `moodlog record 4 -n "日记内容"` | 附带一段日记 |
| `moodlog record 4 -t 工作 -t 运动` | 添加多个标签 |
| `moodlog record 3 -d 2026-05-08` | 指定日期补记 |
| `moodlog record 5 --force` | 覆盖当天已有记录 |

### 查看

| 命令 | 说明 |
|------|------|
| `moodlog today` | 查看今天有没有记录 |
| `moodlog view 2026-05-09` | 查看指定日期 |
| `moodlog view --last 14` | 最近 14 天的列表 |
| `moodlog view --from 2026-05-01 --to 2026-05-31` | 范围内的记录 |
| `moodlog view -s "关键词"` | 在日记和标签里全文搜索 |

### 趋势与统计

| 命令 | 说明 |
|------|------|
| `moodlog trend` | 近 7 天情绪折线图（默认） |
| `moodlog trend 30` | 近 30 天趋势 |
| `moodlog trend --month 5` | 指定月份的折线图 |
| `moodlog stats` | 统计面板：均分、最高/最低日、标签分布、月均情绪 |
| `moodlog stats --calendar` | 统计面板 + 月历热力图 |
| `moodlog stats --month 5` | 指定月份的统计 |

### 月度报告图片

```bash
moodlog report                # 生成本月报告图片
moodlog report -m 5 -y 2026  # 指定月份
```

图片自动保存到 `~/moodlog_reports/moodlog_YYYY_MM.png`，包含日历热力图和情绪折线图两部分。

### 导出

| 命令 | 说明 |
|------|------|
| `moodlog export` | 导出全部记录为 Markdown，直接打印到终端 |
| `moodlog export --format markdown -o diary.md` | 导出为 Markdown 文件 |
| `moodlog export --format json -o data.json` | 导出为 JSON |
| `moodlog export --format csv -o data.csv` | 导出为 CSV |
| `moodlog export --from 2026-05-01 --to 2026-05-31 -o may.csv` | 按日期范围导出 |

### 提醒

| 命令 | 说明 |
|------|------|
| `moodlog remind on` | 开启每日提醒 |
| `moodlog remind on --time 21:00` | 指定提醒时间 |
| `moodlog remind off` | 关闭提醒 |
| `moodlog remind status` | 查看当前提醒状态 |

提醒功能在 Windows 上通过计划任务实现，在 Linux/macOS 上通过 crontab 实现。

### 管理

| 命令 | 说明 |
|------|------|
| `moodlog delete 2026-05-08` | 删除指定日期的记录 |
| `mlog delete` | 删除今天的记录 |
| `moodlog delete --force` | 不询问直接删除今天 |

---

## 多语言

MoodLog 支持中文和英文。切换方法：打开 `moodlog/config.toml`，在文件**最顶层**加入一行：

```toml
language = "en_US"   # 切换为英文
language = "zh_CN"   # 切换回中文
```

修改后重新运行命令即可生效。所有界面文字（提示语、标签、情绪描述、错误信息）均跟随语言设置变化。

---

## 配置说明

`moodlog/config.toml` 首次运行后自动生成，包含以下可调项：

```toml
language = "zh_CN"          # 界面语言：zh_CN 或 en_US

[database]
path = "../../data/moodlog.db"   # 数据库路径，支持绝对路径

[ui]
mood_emoji  = ["😫", "😔", "😐", "😊", "🤩"]   # 各分数对应的 emoji
mood_labels = ["很差", "较差", "一般", "不错", "很棒"]  # 各分数的标签文字
default_trend_days = 7        # trend 命令默认展示天数

[reminder]
enabled = false
time    = "21:00"
```

也可以通过环境变量指定数据库路径：

```bash
export MOODLOG_DB_PATH=/自定义路径/my_moodlog.db
```

---

## 数据结构

每次记录包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | 整数 | 唯一 ID，自增 |
| `date` | 日期 | 记录日期（每日最多一条，可覆盖） |
| `mood_score` | 整数 | 心情评分，1–5（或 100 分彩蛋） |
| `note` | 文本 | 日记正文，可为空 |
| `tags` | 文本列表 | 标签，可多个 |
| `created_at` | 时间戳 | 记录创建时间 |
| `updated_at` | 时间戳 | 最近修改时间 |

数据库文件位于 `data/moodlog.db`，是标准 SQLite 格式，可用任意 SQLite 客户端直接打开。

---

## 项目结构

```
moodlog/
├── config.py                 # 配置读取，支持 TOML + 环境变量
├── database.py               # SQLite CRUD，日期适配器注册
├── models.py                 # MoodEntry / StatsResult 数据类
├── main.py                   # Click CLI 入口
├── __main__.py               # python -m moodlog 入口
├── commands/
│   ├── record.py             # 记录心情
│   ├── view.py               # 查看记录
│   ├── stats.py              # 统计与趋势
│   ├── export.py             # 多格式导出
│   ├── remind.py             # 每日提醒
│   ├── report.py             # matplotlib 月度图片
│   └── delete.py             # 删除记录
├── utils/
│   ├── display.py             # Rich 终端美化输出
│   ├── chart.py              # plotext 折线图
│   ├── art.py                # ASCII 出场动画、可视化评分
│   ├── i18n.py               # 多语言引擎（线程局部存储 + 中文 fallback）
│   ├── report.py             # matplotlib 月度报告
│   └── notify.py              # 跨平台桌面通知
├── locale/
│   ├── zh_CN.json            # 中文翻译（基准）
│   └── en_US.json            # 英文翻译
└── tests/
    ├── test_database.py       # 数据库层 14 个测试
    ├── test_record.py         # record 命令 6 个集成测试
    └── test_stats.py          # stats 命令 6 个集成测试
.github/workflows/ci.yml       # GitHub Actions（Python 3.10–3.13 矩阵）
data/moodlog.db               # 数据库文件（不纳入版本控制）
```

---

## 测试

```bash
pytest                       # 运行全部测试
pytest --cov=moodlog          # 带覆盖率
pytest --cov=moodlog --cov-report=html  # HTML 报告
```

当前测试覆盖：27 个用例，涵盖数据库操作、record 命令、stats 命令。覆盖率 53%，部分工具模块（如 notify、report 交互部分）暂未纳入测试。

---

## 技术选型

| 用途 | 工具 | 说明 |
|------|------|------|
| 命令行界面 | Click 8 | 声明式子命令，支持嵌套 |
| 终端美化 | Rich 13 | 表格、颜色、面板、月历 |
| 终端折线图 | plotext 5 | 直接在终端绘图，无依赖额外图形库 |
| 月度报告图 | matplotlib | 非交互 Agg 后端，无需显示器 |
| 数据存储 | SQLite（标准库） | 单文件，无须额外部署 |
| 桌面通知 | plyer | Windows / macOS / Linux 通用 |
| 配置格式 | tomllib | Python 3.11+ 标准库，TOML 1.0 |
| 测试框架 | pytest + pytest-cov | 单元测试 + 集成测试 + 覆盖率 |
| CI | GitHub Actions | 推送/PR 自动触发，Python 3.10–3.13 全矩阵 |

---

## 常见问题

**Q：每天可以记录多条吗？**
不可以。每日期最多保留一条记录，使用 `--force` 可以覆盖当天已有内容。

**Q：数据存在哪里？**
默认在 `data/moodlog.db`，是 SQLite 文件。在 `config.toml` 的 `[database]` 部分可以修改路径。

**Q：如何备份数据？**
直接复制 `data/moodlog.db` 文件即可。这是标准 SQLite 数据库，也可以用 `sqlite3 moodlog.db .dump` 导出为 SQL 文本。

**Q：提醒功能怎么用？**
运行 `moodlog remind on` 后，程序会自动在系统注册一个定时任务（Windows 用任务计划程序，Linux/macOS 用 crontab）。每日到达设定时间会弹出一个桌面通知。

**Q：matplotlib 报告图存到哪里了？**
默认保存到用户主目录下的 `moodlog_reports/` 文件夹：`~/moodlog_reports/moodlog_YYYY_MM.png`。

---

## 开发记录

| 阶段 | 内容 | 状态 |
|------|------|------|
| 第一阶段 | 项目骨架、数据库、record、today | 完成 |
| 第二阶段 | 标签、搜索、view、stats、export | 完成 |
| 第三阶段 | Rich 美化、提醒、单元测试、pyproject 打包 | 完成 |
| 第四阶段 | GitHub Actions CI、多语言（i18n）、matplotlib 月度报告、ASCII 出场动画 | 完成 |

---

## 彩蛋 🥚

MoodLog 隐藏了一个彩蛋：给自己打个 **100 分** 试试？

```bash
moodlog record 100
```

**会发生什么：**
- 进度条变成满格，文字变成 `100⭐ 🚀 宇宙无敌爆炸开心`
- 日历里那天会显示 🚀 emoji
- 所有统计数据自动排除 100 分（避免图表失真），均值、最高/最低日判断不受影响
- 导出时正常导出为 `mood_score = 100`

**为什么有这个彩蛋：**
有些日子特别特别好，值得一个专属的标记。如果今天你真的感觉"爱这个世界"，就给自己 100 分吧。

---

## License

MIT
