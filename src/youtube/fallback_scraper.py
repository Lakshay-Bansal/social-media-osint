import re
from datetime import datetime
from typing import List, Optional, Tuple
from ..config import Config
from ..utils.formatters import format_duration, safe_int
from ..utils.logger import setup_logger
from .models import YouTubeChannel, YouTubeVideo

logger = setup_logger("youtube_fallback")


class YouTubeFallbackExtractor:
    """
    Fallback YouTube channel extractor using yt-dlp.
    Extracts channel metadata, video list, durations, and view counts
    without requiring a Google API Key.
    """

    def __init__(self):
        pass

    def extract_channel_and_videos(
        self,
        identifier: str,
        max_videos: int = 50,
    ) -> Tuple[YouTubeChannel, List[YouTubeVideo]]:
        """
        Extract channel information and recent videos via yt-dlp.
        identifier can be @handle, channel URL, or UC... ID.
        """
        try:
            import yt_dlp
        except ImportError:
            raise RuntimeError(
                "yt-dlp is required for keyless YouTube extraction. "
                "Install it with `pip install yt-dlp`."
            )

        channel_url = self._normalize_channel_url(identifier)
        logger.info(f"Extracting channel data via yt-dlp: {channel_url}")

        ydl_opts = {
            "extract_flat": "in_playlist",
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "playlist_items": f"1-{max_videos}",
            "ignoreerrors": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            if not info:
                raise ValueError(f"Could not extract channel data for: {identifier}")

        channel_id = info.get("channel_id") or info.get("id") or "unknown"
        channel_title = info.get("channel") or info.get("uploader") or info.get("title") or identifier
        custom_url = info.get("channel_url") or info.get("uploader_url") or channel_url
        description = info.get("description") or ""

        # Some channels don't expose sub count in flat extraction
        subscriber_count = safe_int(info.get("channel_follower_count"))
        video_count = safe_int(info.get("playlist_count")) or safe_int(info.get("video_count"))

        entries = info.get("entries") or []
        videos: List[YouTubeVideo] = []

        for entry in entries:
            if not entry or not isinstance(entry, dict):
                continue

            v_id = entry.get("id")
            if not v_id:
                continue

            title = entry.get("title") or "Untitled"
            desc = entry.get("description") or ""
            duration = safe_int(entry.get("duration"))
            views = safe_int(entry.get("view_count"))
            likes = safe_int(entry.get("like_count"))
            comments = safe_int(entry.get("comment_count"))
            raw_date = entry.get("upload_date") or entry.get("release_date")
            pub_date = self._format_upload_date(raw_date)

            is_short = duration <= Config.SHORTS_THRESHOLD_SECONDS and duration > 0
            if "/shorts/" in (entry.get("url") or "") or "#shorts" in title.lower():
                is_short = True

            video = YouTubeVideo(
                video_id=v_id,
                title=title,
                description=desc[:500] if desc else "",
                published_at=pub_date,
                duration_seconds=duration,
                duration_formatted=format_duration(duration),
                is_short=is_short,
                view_count=views,
                like_count=likes,
                comment_count=comments,
                url=f"https://www.youtube.com/watch?v={v_id}",
                thumbnail_url=entry.get("thumbnail") or f"https://i.ytimg.com/vi/{v_id}/hqdefault.jpg",
            )
            videos.append(video)

        total_views = sum(v.view_count for v in videos)
        channel = YouTubeChannel(
            channel_id=channel_id,
            title=channel_title,
            custom_url=custom_url,
            description=description,
            published_at="N/A",
            subscriber_count=subscriber_count,
            video_count=video_count or len(videos),
            view_count=total_views,
            videos=videos,
        )

        return channel, videos

    def _normalize_channel_url(self, identifier: str) -> str:
        """Convert input identifier to standard YouTube channel URL."""
        identifier = identifier.strip()
        if identifier.startswith("http://") or identifier.startswith("https://"):
            return identifier
        if identifier.startswith("@"):
            return f"https://www.youtube.com/{identifier}/videos"
        if identifier.startswith("UC") and len(identifier) >= 20:
            return f"https://www.youtube.com/channel/{identifier}/videos"
        return f"https://www.youtube.com/@{identifier}/videos"

    def _format_upload_date(self, raw_date: Optional[str]) -> str:
        """Format YYYYMMDD into YYYY-MM-DD."""
        if not raw_date:
            return "N/A"
        raw_str = str(raw_date)
        if len(raw_str) == 8 and raw_str.isdigit():
            return f"{raw_str[:4]}-{raw_str[4:6]}-{raw_str[6:]}"
        return raw_str
