# Grafana Dashboard Setup Guide

This project includes ready-to-import Grafana configurations that connect seamlessly to the SQLite database automatically exported by the Social Media OSINT toolkit (`data/social_osint.sqlite`).

---

## 1. Prerequisites

- **Grafana Server**: Running locally or via Docker (`docker run -d -p 3000:3000 grafana/grafana`)
- **Grafana SQLite Plugin**: Install the official `frser-sqlite-datasource` plugin:
  ```bash
  grafana-cli plugins install frser-sqlite-datasource
  ```
  *(Or restart your Grafana container with `GF_INSTALL_PLUGINS=frser-sqlite-datasource`)*

---

## 2. Setting Up the Data Source

1. In Grafana, navigate to **Connections** > **Data Sources** > **Add data source**.
2. Search for **SQLite**.
3. Configure the following fields:
   - **Name**: `SQLite OSINT`
   - **UID**: `sqlite-osint`
   - **Path**: Absolute path to your database file:
     - Windows example: `E:\Project\social-media-osint\data\social_osint.sqlite`
     - Linux/Docker example: `/var/data/social_osint.sqlite`
4. Click **Save & Test** to verify connection.

---

## 3. Importing the Dashboard

1. Navigate to **Dashboards** > **New** > **Import**.
2. Click **Upload JSON file** and select [`youtube_osint_dashboard.json`](file:///e:/Project/social-media-osint/grafana/youtube_osint_dashboard.json).
3. Select your `SQLite OSINT` data source.
4. Click **Import**.

---

## 4. Included Panels & Metrics

- **Subscribers Stat Widget**: Live subscriber count.
- **Total Channel Uploads Widget**: Lifetime videos on the channel.
- **Shorts Count (≤60s)**: Total count and proportion of short-form content.
- **Regular Videos (>60s)**: Long-form content count.
- **Total Views**: Sum of views across all analyzed videos.
- **Top 10 Most Viewed Videos Table**: Title, formatted duration, view count, likes, upload date, link.
- **Top 10 Longest Videos Table**: Deep dive into long-form content.
- **Top 10 Most Viewed Shorts Table**: Filtered solely for vertical / short-form content.

---

> [!TIP]
> You can also use the built-in interactive **Streamlit Dashboard** (`streamlit run dashboard.py`), which requires zero external servers and launches instantly with interactive sorting and filters.
