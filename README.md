# Social Media OSINT & Channel Analytics Suite

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](VERSION)
[![Python](https://img.shields.io/badge/python-3.12-brightgreen.svg)](ENVIRONMENT.md)
[![Environment](https://img.shields.io/badge/conda%20env-yio-orange.svg)](ENVIRONMENT.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An enterprise-grade, modular Open Source Intelligence (OSINT) and statistical analysis toolkit for **YouTube Channels** and **Instagram Profiles**. Designed specifically for deep content analysis, Shorts vs long-form video categorization, duration distributions, view analytics, sortable data tables, and interactive dashboards.

---

## 🚀 Key Features

### 📺 YouTube Channel OSINT
- **Channel Profiling**: Channel title, handle (`@username`), subscriber count, total channel uploads, account creation date, bio description, avatar, and banner.
- **Videos vs. Shorts Breakdown**:
  - Exact count and percentage of **Shorts** (duration $\le 60$s or `#shorts` format).
  - Exact count of **Regular Long-Form Videos** (duration $> 60$s).
- **Video Duration & Length Analysis**:
  - Total catalog duration (formatted in hours and `HH:MM:SS`).
  - Average video duration, median duration, longest video, shortest video.
  - Sub-segment analysis: Average Regular Video length vs Average Short length.
- **Top 10 Leaderboard & Custom Sorting**:
  - Top 10 Most Viewed videos.
  - Top 10 Longest videos.
  - Top 10 Shortest videos.
  - Top 10 Most Viewed Shorts.
  - Top 10 Most Liked videos.
- **Dual Extraction Engine**:
  - **YouTube Data API v3** (High-speed batching of 50 items/request, exact ISO 8601 duration parsing).
  - **Automatic Fallback Scraper (`yt-dlp`)** (Works seamlessly out-of-the-box even **without** an API key!).

### 📸 Instagram Profile OSINT
- **Profile Metrics**: Follower count, following count, total post count, account verification status, privacy status, business account flag, and bio.
- **Post Classification**: Categorization into **Photos**, **Reels**, **Videos**, and **Carousel** multi-item posts.
- **Engagement Rate Analysis**: Ratio of likes & comments relative to audience size.
- **Recent Post Inspection**: Upload dates, like counts, comment counts, and media URLs.

### 📊 Modern Interactive Dashboards
1. **Interactive Web Dashboard (`Streamlit` + `Plotly`)**:
   - Zero-setup web app with KPI cards, donut charts, duration distribution histograms, monthly upload timelines, real-time title search, sortable tables, and one-click CSV/JSON/SQLite exports.
2. **Grafana Integration**:
   - Pre-built Grafana dashboard JSON template in [`grafana/youtube_osint_dashboard.json`](grafana/youtube_osint_dashboard.json) connecting to the generated SQLite database.

---

## 📁 Project Architecture

```
social-media-osint/
├── .env.example              # Template for environment credentials
├── .gitignore                # Git ignore rules for virtualenvs, data, and cache
├── ENVIRONMENT.md            # Reference guide for conda environment 'yio'
├── VERSION                   # Semantic version definition (1.0.0)
├── requirements.txt          # Python dependencies
├── README.md                 # Complete documentation & setup guide
├── main.py                   # Interactive CLI entrypoint (outside src/)
├── dashboard.py              # Modern interactive Streamlit web dashboard
├── grafana/
│   ├── README.md             # Grafana connection guide
│   └── youtube_osint_dashboard.json # Ready-to-import Grafana dashboard
├── data/
│   └── .gitkeep              # Directory for exported JSON, CSV, and SQLite DBs
└── src/
    ├── __init__.py           # Package root
    ├── config.py             # Configuration & environment variable loader
    ├── youtube/              # YouTube extraction & data models
    │   ├── __init__.py
    │   ├── models.py         # YouTubeChannel & YouTubeVideo dataclasses
    │   ├── client.py         # YouTube Data API v3 client with batching
    │   └── fallback_scraper.py # yt-dlp keyless fallback engine
    ├── instagram/            # Instagram OSINT & data models
    │   ├── __init__.py
    │   ├── models.py         # InstagramProfile & InstagramPost dataclasses
    │   └── client.py         # Instaloader & public meta client
    ├── analytics/            # Statistical & aggregation engines
    │   ├── __init__.py
    │   ├── channel_analyzer.py # YouTube statistical & duration analyzer
    │   └── metrics.py        # Instagram post & engagement analyzer
    ├── utils/                # Formatting, storage & logging helpers
    │   ├── __init__.py
    │   ├── formatters.py     # ISO 8601 duration parser & number formatters
    │   ├── storage.py        # JSON, CSV, and SQLite multi-format exporter
    │   └── logger.py         # Standardized logger
    └── ui/                   # Terminal presentations
        ├── __init__.py
        └── terminal.py       # Rich terminal panels & formatted tables
```

---

## 🛠️ Setup & Installation Guide

### Step 1: Create & Activate Conda Environment (`yio`)

The project uses a dedicated Conda environment named **`yio`** (Python 3.12):

```bash
# Create the yio conda environment
conda create -n yio python=3.12 -y

# Activate the environment
conda activate yio
```

### Step 2: Install Dependencies

With `yio` active, install all required packages:

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Copy `.env.example` to create your local `.env`:

```bash
cp .env.example .env
```

Edit `.env` to configure your keys:
```env
# Optional: YouTube Data API v3 Key (from Google Cloud Console)
# If left empty, the tool automatically uses the yt-dlp fallback scraper!
YOUTUBE_API_KEY=your_api_key_here

# Optional: Instagram credentials (for authenticated sessions)
INSTAGRAM_USERNAME=
INSTAGRAM_PASSWORD=

# Scanning defaults
DEFAULT_MAX_VIDEOS=200
OUTPUT_DIR=data
```

> [!TIP]
> **API Key is Optional**: If you don't have a YouTube API key right now, leave `YOUTUBE_API_KEY=` blank. The engine will automatically switch to the intelligent fallback extractor without interrupting your workflow!

---

## 💻 Usage

### 1. Interactive Command-Line Interface (`main.py`)

Run the main CLI interactive interface:

```bash
conda activate yio
python main.py
```

The interactive menu prompts you for:
- Target channel handle (`@veritasium`, `@MrBeast`), Channel ID (`UC...`), or channel URL.
- Number of recent videos to analyze.
- Real-time display of KPI panel and interactive selection of **Top 10** tables (Most Viewed, Longest, Shortest, Shorts only, Most Liked).
- Multi-format data export (JSON, CSV, SQLite).

### 2. Interactive Web Dashboard (`dashboard.py`)

Launch the Streamlit web dashboard:

```bash
conda activate yio
streamlit run dashboard.py
```

Or select **Option [3]** directly inside `main.py`!

Features in the Dashboard:
- **Sidebar Control**: Enter any YouTube channel or Instagram username and hit Analyze.
- **KPI Metrics Cards**: Sub count, upload count, total views, Shorts vs regular count, total hours, average duration.
- **Plotly Visuals**: Shorts vs Videos donut chart, duration distribution histogram, upload frequency over time.
- **Top 10 Tabs**: Instant switching between Top 10 Most Viewed, Top 10 Longest, Top 10 Shortest, Top 10 Shorts, and Top 10 Liked.
- **Searchable, Sortable Table**: Filter by video type (Shorts vs Long), search by title keywords, and sort by views, duration, or date.
- **Direct Downloads**: Download CSV, JSON, or save directly to SQLite.

### 3. Grafana Dashboard

To view channel statistics in **Grafana**:
1. Scan your channels using `main.py` or `dashboard.py` (which populates `data/social_osint.sqlite`).
2. Follow the setup instructions in [`grafana/README.md`](grafana/README.md).
3. Import the dashboard JSON from [`grafana/youtube_osint_dashboard.json`](grafana/youtube_osint_dashboard.json).

---

## 📈 Data Models & Metrics Explained

| Metric | Description | Formula / Rule |
| :--- | :--- | :--- |
| **Shorts Count** | Total number of vertical / short-form videos | $\text{duration} \le 60\text{s}$ or `#shorts` |
| **Regular Videos** | Traditional long-form videos | $\text{duration} > 60\text{s}$ |
| **Duration Formatted** | Human-readable video length | `HH:MM:SS` or `MM:SS` |
| **Total Duration** | Combined watch length of all analyzed videos | $\sum \text{duration}$ in hours |
| **Average Duration** | Mean video length across analyzed content | $\frac{\sum \text{duration}}{N}$ |
| **Engagement Rate** | Post interaction intensity (Instagram) | $\frac{\text{Likes} + \text{Comments}}{\text{Followers}} \times 100\%$ |

---

## 🧪 Testing & Verification

To run a fast test on the analyzer and utilities:

```bash
conda activate yio
python -c "from src.youtube.models import YouTubeVideo; from src.analytics.channel_analyzer import YouTubeChannelAnalyzer; print('Modules imported cleanly!')"
```

---

## 📝 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
