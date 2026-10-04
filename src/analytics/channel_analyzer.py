from collections import Counter
from datetime import datetime
from statistics import mean, median
from typing import Any, Dict, List, Optional
import pandas as pd
from ..youtube.models import YouTubeChannel, YouTubeVideo
from ..utils.formatters import format_duration, format_number, safe_int


class YouTubeChannelAnalyzer:
    """
    In-depth statistical analysis engine for YouTube channel OSINT data.
    Computes video vs shorts breakdown, duration distributions, view analytics,
    and leaderboard rankings.
    """

    def __init__(self, channel: YouTubeChannel, videos: Optional[List[YouTubeVideo]] = None):
        self.channel = channel
        self.videos = videos or channel.videos
        self._df: Optional[pd.DataFrame] = None

    @property
    def dataframe(self) -> pd.DataFrame:
        """Construct or return cached Pandas DataFrame of all analyzed videos."""
        if self._df is None:
            data = [v.to_dict() for v in self.videos]
            if not data:
                self._df = pd.DataFrame(
                    columns=[
                        "video_id", "title", "published_at", "duration_seconds",
                        "duration_formatted", "is_short", "view_count",
                        "like_count", "comment_count", "url", "description",
                    ]
                )
            else:
                df = pd.DataFrame(data)
                # Ensure numeric types
                df["duration_seconds"] = pd.to_numeric(df["duration_seconds"], errors="coerce").fillna(0).astype(int)
                df["view_count"] = pd.to_numeric(df["view_count"], errors="coerce").fillna(0).astype(int)
                df["like_count"] = pd.to_numeric(df["like_count"], errors="coerce").fillna(0).astype(int)
                df["comment_count"] = pd.to_numeric(df["comment_count"], errors="coerce").fillna(0).astype(int)
                df["is_short"] = df["is_short"].astype(bool)
                self._df = df
        return self._df

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Compute comprehensive high-level metrics for the channel."""
        total_analyzed = len(self.videos)
        if total_analyzed == 0:
            return {
                "channel_id": self.channel.channel_id,
                "title": self.channel.title,
                "custom_url": self.channel.custom_url,
                "total_channel_videos": self.channel.video_count,
                "total_analyzed_videos": 0,
                "shorts_count": 0,
                "regular_videos_count": 0,
                "shorts_percentage": 0.0,
                "total_views_analyzed": 0,
                "avg_views_per_video": 0,
                "median_views": 0,
                "total_duration_seconds": 0,
                "total_duration_hours": 0.0,
                "avg_duration_seconds": 0,
                "avg_duration_formatted": "00:00",
                "median_duration_formatted": "00:00",
                "max_duration_formatted": "00:00",
                "min_duration_formatted": "00:00",
            }

        df = self.dataframe
        shorts_df = df[df["is_short"] == True]
        regular_df = df[df["is_short"] == False]

        shorts_count = int(len(shorts_df))
        regular_count = int(len(regular_df))
        shorts_pct = round((shorts_count / total_analyzed) * 100, 1)

        durations = df["duration_seconds"].tolist()
        total_duration_secs = sum(durations)
        avg_duration_secs = int(mean(durations)) if durations else 0
        med_duration_secs = int(median(durations)) if durations else 0
        max_duration_secs = max(durations) if durations else 0
        min_duration_secs = min(durations) if durations else 0

        views = df["view_count"].tolist()
        total_views_analyzed = sum(views)
        avg_views = int(mean(views)) if views else 0
        med_views = int(median(views)) if views else 0

        # Duration subsets
        avg_regular_secs = int(regular_df["duration_seconds"].mean()) if not regular_df.empty else 0
        avg_shorts_secs = int(shorts_df["duration_seconds"].mean()) if not shorts_df.empty else 0

        return {
            "channel_id": self.channel.channel_id,
            "title": self.channel.title,
            "custom_url": self.channel.custom_url,
            "subscribers": self.channel.subscriber_count,
            "total_channel_videos": self.channel.video_count,
            "total_analyzed_videos": total_analyzed,
            "shorts_count": shorts_count,
            "regular_videos_count": regular_count,
            "shorts_percentage": shorts_pct,
            "total_views_analyzed": total_views_analyzed,
            "avg_views_per_video": avg_views,
            "median_views": med_views,
            "total_duration_seconds": total_duration_secs,
            "total_duration_hours": round(total_duration_secs / 3600, 2),
            "avg_duration_seconds": avg_duration_secs,
            "avg_duration_formatted": format_duration(avg_duration_secs),
            "median_duration_formatted": format_duration(med_duration_secs),
            "max_duration_formatted": format_duration(max_duration_secs),
            "min_duration_formatted": format_duration(min_duration_secs),
            "avg_regular_duration_formatted": format_duration(avg_regular_secs),
            "avg_shorts_duration_formatted": format_duration(avg_shorts_secs),
        }

    def get_top_videos_by_views(self, limit: int = 10) -> pd.DataFrame:
        """Return top N most viewed videos."""
        df = self.dataframe
        if df.empty:
            return df
        return df.sort_values(by="view_count", ascending=False).head(limit)

    def get_top_videos_by_duration(self, limit: int = 10, longest: bool = True) -> pd.DataFrame:
        """Return top N longest or shortest videos."""
        df = self.dataframe
        if df.empty:
            return df
        return df.sort_values(by="duration_seconds", ascending=not longest).head(limit)

    def get_top_videos_by_likes(self, limit: int = 10) -> pd.DataFrame:
        """Return top N most liked videos."""
        df = self.dataframe
        if df.empty:
            return df
        return df.sort_values(by="like_count", ascending=False).head(limit)

    def get_top_shorts_by_views(self, limit: int = 10) -> pd.DataFrame:
        """Return top N most viewed YouTube Shorts."""
        df = self.dataframe
        if df.empty:
            return df
        shorts_df = df[df["is_short"] == True]
        return shorts_df.sort_values(by="view_count", ascending=False).head(limit)

    def get_upload_timeline_metrics(self) -> Dict[str, Any]:
        """Compute upload frequency across years, months, and days of the week."""
        df = self.dataframe
        if df.empty:
            return {"by_year": {}, "by_month": {}, "by_day_of_week": {}}

        dates = []
        for val in df["published_at"]:
            try:
                dt = datetime.fromisoformat(str(val).replace("Z", "+00:00")[:10])
                dates.append(dt)
            except Exception:
                continue

        if not dates:
            return {"by_year": {}, "by_month": {}, "by_day_of_week": {}}

        years = Counter(dt.strftime("%Y") for dt in dates)
        months = Counter(dt.strftime("%Y-%m") for dt in dates)
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        days = Counter(day_names[dt.weekday()] for dt in dates)

        return {
            "first_upload": min(dates).strftime("%Y-%m-%d"),
            "latest_upload": max(dates).strftime("%Y-%m-%d"),
            "by_year": dict(sorted(years.items())),
            "by_month": dict(sorted(months.items())),
            "by_day_of_week": {day: days.get(day, 0) for day in day_names},
        }
