import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from ..config import Config


class DataExporter:
    """Handles serialization and export of OSINT data to JSON, CSV, and SQLite."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Config.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_to_json(self, data: Dict[str, Any], filename_prefix: str) -> Path:
        """Export raw and analyzed data dictionary to structured JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_prefix = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in filename_prefix)
        filename = f"{safe_prefix}_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)

        return filepath

    def export_videos_to_csv(self, videos_data: List[Dict[str, Any]], filename_prefix: str) -> Path:
        """Export list of video records to CSV."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_prefix = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in filename_prefix)
        filename = f"{safe_prefix}_videos_{timestamp}.csv"
        filepath = self.output_dir / filename

        df = pd.DataFrame(videos_data)
        df.to_csv(filepath, index=False, encoding="utf-8")
        return filepath

    def export_to_sqlite(
        self,
        channel_info: Dict[str, Any],
        videos_data: List[Dict[str, Any]],
        db_name: str = "social_osint.sqlite",
    ) -> Path:
        """
        Store channel information and video records in a SQLite database.
        This provides instant compatibility with Grafana SQLite data source,
        BI tools, and relational analysis.
        """
        db_path = self.output_dir / db_name
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create channels table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS channels (
                channel_id TEXT PRIMARY KEY,
                title TEXT,
                custom_url TEXT,
                description TEXT,
                published_at TEXT,
                subscriber_count INTEGER,
                video_count INTEGER,
                view_count INTEGER,
                country TEXT,
                updated_at TEXT
            )
            """
        )

        # Create videos table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS youtube_videos (
                video_id TEXT PRIMARY KEY,
                channel_id TEXT,
                title TEXT,
                description TEXT,
                published_at TEXT,
                duration_seconds INTEGER,
                duration_formatted TEXT,
                is_short INTEGER,
                view_count INTEGER,
                like_count INTEGER,
                comment_count INTEGER,
                url TEXT,
                updated_at TEXT,
                FOREIGN KEY (channel_id) REFERENCES channels (channel_id)
            )
            """
        )

        # Insert or replace channel
        cursor.execute(
            """
            INSERT OR REPLACE INTO channels (
                channel_id, title, custom_url, description, published_at,
                subscriber_count, video_count, view_count, country, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                channel_info.get("channel_id"),
                channel_info.get("title"),
                channel_info.get("custom_url"),
                channel_info.get("description"),
                str(channel_info.get("published_at")),
                channel_info.get("subscriber_count", 0),
                channel_info.get("video_count", 0),
                channel_info.get("view_count", 0),
                channel_info.get("country"),
                datetime.utcnow().isoformat(),
            ),
        )

        # Insert or replace videos
        for v in videos_data:
            cursor.execute(
                """
                INSERT OR REPLACE INTO youtube_videos (
                    video_id, channel_id, title, description, published_at,
                    duration_seconds, duration_formatted, is_short,
                    view_count, like_count, comment_count, url, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    v.get("video_id"),
                    channel_info.get("channel_id"),
                    v.get("title"),
                    v.get("description"),
                    str(v.get("published_at")),
                    v.get("duration_seconds", 0),
                    v.get("duration_formatted", ""),
                    1 if v.get("is_short") else 0,
                    v.get("view_count", 0),
                    v.get("like_count", 0),
                    v.get("comment_count", 0),
                    v.get("url"),
                    datetime.utcnow().isoformat(),
                ),
            )

        conn.commit()
        conn.close()
        return db_path
