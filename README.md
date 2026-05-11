# MoodLog

> A mood diary for your terminal. Track emotions, spot patterns.

[中文文档](README_zh.md)

---

## What is MoodLog

MoodLog is a command-line mood tracking tool.

Each day, give yourself a score from 1–5, optionally with a short diary entry or a few tags. Over time, use the built-in stats, trend charts, and monthly reports to look back: which days were best, which tags keep showing up, how your mood has been trending.

All data stays in a local SQLite database — nothing goes online, nothing gets uploaded. The database file lives at `data/moodlog.db`, and you can back it up or migrate it anytime.

---

## Installation

```bash
# Clone the repo
git clone https://github.com/Linrane/moodlog.git
cd moodlog

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate

# Install
pip install -e ".[dev]"
```

Once installed, just type `moodlog` in your terminal from anywhere. On first run, a config file `config.toml` will be created automatically in the `moodlog/` directory.

---

## Quick Start

Log today's mood (just a number, done in 10 seconds):

```bash
moodlog record 4
```

With a diary entry and tags:

```bash
moodlog record 4 -n "Project launched today, everything went smoothly" -t work
```

No score? An interactive prompt will guide you:

```bash
moodlog record
```

---

## Command Overview

### Recording

| Command | Description |
|---------|-------------|
| `moodlog record [score]` | Log today's mood. Score 1–5, or omit to enter interactive mode |
| `moodlog record 4 -n "diary text"` | Add a diary entry |
| `moodlog record 4 -t work -t exercise` | Add multiple tags |
| `moodlog record 3 -d 2026-05-08` | Backfill a past date |
| `moodlog record 5 --force` | Overwrite today's entry |

### Viewing

| Command | Description |
|---------|-------------|
| `moodlog today` | Check if you've logged today |
| `moodlog view 2026-05-09` | View a specific date |
| `moodlog view --last 14` | List last 14 days |
| `moodlog view --from 2026-05-01 --to 2026-05-31` | View a date range |
| `moodlog view -s "keyword"` | Search diary and tags |

### Trends & Stats

| Command | Description |
|---------|-------------|
| `moodlog trend` | 7-day mood line chart (default) |
| `moodlog trend 30` | 30-day trend |
| `moodlog trend --month 5` | Specified month's trend |
| `moodlog stats` | Stats panel: average, best/worst days, tag distribution, monthly averages |
| `moodlog stats --calendar` | Stats panel + monthly calendar heatmap |
| `moodlog stats --month 5` | Stats for a specific month |

### Monthly Report Image

```bash
moodlog report                # Generate this month's report image
moodlog report -m 5 -y 2026  # Specify month and year
```

Images are saved to `~/moodlog_reports/moodlog_YYYY_MM.png`, containing a calendar heatmap and a mood trend line chart.

### Export

| Command | Description |
|---------|-------------|
| `moodlog export` | Export all entries as Markdown (printed to terminal) |
| `moodlog export --format markdown -o diary.md` | Export as Markdown file |
| `moodlog export --format json -o data.json` | Export as JSON |
| `moodlog export --format csv -o data.csv` | Export as CSV |
| `moodlog export --from 2026-05-01 --to 2026-05-31 -o may.csv` | Export by date range |

### Reminder

| Command | Description |
|---------|-------------|
| `moodlog remind on` | Enable daily reminder |
| `moodlog remind on --time 21:00` | Set reminder time |
| `moodlog remind off` | Disable reminder |
| `moodlog remind status` | Check reminder status |

Reminders use scheduled tasks on Windows and crontab on Linux/macOS.

### Management

| Command | Description |
|---------|-------------|
| `moodlog delete 2026-05-08` | Delete a specific date's entry |
| `mlog delete` | Delete today's entry |
| `moodlog delete --force` | Delete today without confirmation |

---

## Multi-language

MoodLog supports Chinese and English. To switch, open `moodlog/config.toml` and add this line at the **top** of the file:

```toml
language = "en_US"   # Switch to English
language = "zh_CN"   # Switch back to Chinese
```

The change takes effect immediately on next run. All interface text (prompts, labels, mood descriptions, error messages) will follow the language setting.

---

## Configuration

`moodlog/config.toml` is auto-generated on first run. Available settings:

```toml
language = "zh_CN"          # Interface language: zh_CN or en_US

[database]
path = "../../data/moodlog.db"   # Database path, supports absolute paths

[ui]
mood_emoji  = ["😫", "😔", "😐", "😊", "🤩"]   # Emoji for each score
mood_labels = ["Very Bad", "Not Great", "Okay", "Good", "Amazing"]  # Labels for each score
default_trend_days = 7        # Default number of days for trend command

[reminder]
enabled = false
time    = "21:00"
```

You can also specify the database path via environment variable:

```bash
export MOODLOG_DB_PATH=/custom/path/my_moodlog.db
```

---

## Data Structure

Each entry contains the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Unique ID, auto-increment |
| `date` | Date | Record date (one per day, can overwrite) |
| `mood_score` | Integer | Mood score, 1–5 (or 100 for the easter egg) |
| `note` | Text | Diary text, can be empty |
| `tags` | Text list | Tags, can be multiple |
| `created_at` | Timestamp | Record creation time |
| `updated_at` | Timestamp | Last modification time |

The database file is at `data/moodlog.db`, standard SQLite format, openable with any SQLite client.

---

## Project Structure

```
moodlog/
├── config.py                 # Config reader, supports TOML + env vars
├── database.py               # SQLite CRUD, date adapter registration
├── models.py                 # MoodEntry / StatsResult data classes
├── main.py                   # Click CLI entry point
├── __main__.py               # python -m moodlog entry point
├── commands/
│   ├── record.py             # Record mood
│   ├── view.py               # View records
│   ├── stats.py              # Stats and trends
│   ├── export.py             # Multi-format export
│   ├── remind.py             # Daily reminders
│   ├── report.py             # matplotlib monthly images
│   └── delete.py             # Delete records
├── utils/
│   ├── display.py             # Rich terminal output
│   ├── chart.py              # plotext line charts
│   ├── art.py                # ASCII animations, visual score picker
│   ├── i18n.py               # i18n engine (thread-local + Chinese fallback)
│   ├── report.py             # matplotlib monthly report
│   └── notify.py              # Cross-platform desktop notifications
├── locale/
│   ├── zh_CN.json            # Chinese translations (baseline)
│   └── en_US.json            # English translations
└── tests/
    ├── test_database.py       # Database layer, 14 tests
    ├── test_record.py         # record command, 6 integration tests
    └── test_stats.py          # stats command, 6 integration tests
.github/workflows/ci.yml       # GitHub Actions (Python 3.10–3.13 matrix)
data/moodlog.db               # Database file (not version controlled)
```

---

## Testing

```bash
pytest                       # Run all tests
pytest --cov=moodlog          # With coverage
pytest --cov=moodlog --cov-report=html  # HTML coverage report
```

Current test suite: 27 test cases, covering database operations, record command, and stats command. Coverage is 53%; some utility modules (notify, report interaction) are not yet included.

---

## Tech Stack

| Purpose | Tool | Notes |
|---------|------|-------|
| CLI | Click 8 | Declarative subcommands, supports nesting |
| Terminal UI | Rich 13 | Tables, colors, panels, calendar |
| Terminal charts | plotext 5 | In-terminal plotting, no extra graphics libs |
| Monthly reports | matplotlib | Non-interactive Agg backend, no display needed |
| Data storage | SQLite (stdlib) | Single file, no extra deployment |
| Desktop notifications | plyer | Windows / macOS / Linux compatible |
| Config format | tomllib | Python 3.11+ stdlib, TOML 1.0 |
| Testing | pytest + pytest-cov | Unit tests + integration tests + coverage |
| CI | GitHub Actions | Triggered on push/PR, Python 3.10–3.13 full matrix |

---

## FAQ

**Q: Can I record multiple entries per day?**
No. At most one entry per day. Use `--force` to overwrite an existing entry.

**Q: Where is my data stored?**
By default at `data/moodlog.db`, a SQLite file. You can change the path in `config.toml` under the `[database]` section.

**Q: How do I back up my data?**
Just copy the `data/moodlog.db` file. It's a standard SQLite database. You can also use `sqlite3 moodlog.db .dump` to export as SQL text.

**Q: How does the reminder feature work?**
After running `moodlog remind on`, the program registers a scheduled task (Task Scheduler on Windows, crontab on Linux/macOS). At the set time each day, a desktop notification will pop up.

**Q: Where are the matplotlib report images saved?**
By default to `~/moodlog_reports/moodlog_YYYY_MM.png`.

---

## Easter Egg

MoodLog has a hidden easter egg: try giving yourself a **score of 100**!

```bash
moodlog record 100
```

**What happens:**
- The progress bar goes full, text becomes `100⭐ 🚀 Universe-Invincible-Explosion-Happy`
- That day shows 🚀 in the calendar view
- All stats automatically exclude the 100 score (to avoid chart distortion), but averages and best/worst day calculations are not affected
- Exports normally as `mood_score = 100`

**Why this easter egg:**
Some days are just extraordinarily good — they deserve a special marker. If today you really feel like "loving this world," give yourself 100 points.

---

## License

MIT
