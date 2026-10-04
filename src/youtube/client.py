import re
from typing import Any, Callable, Dict, List, Optional, Tuple
from ..config import Config
from ..utils.formatters import (
    format_datetime,
    format_duration,
    parse_iso_duration,
    safe_int,
)
from ..utils.logger import setup_logger
from .fallback_scraper import YouTubeFallbackExtractor
from .models import YouTubeChannel, YouTubeVideo

logger = setup_logger("youtube_client")


class YouTubeOSINTClient:
    """
    Primary YouTube OSINT Client.
    Uses YouTube Data API v3 when an API key is available,
    with automatic graceful fallback to yt-dlp scraping.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or Config.YOUTUBE_API_KEY).strip()
        self._service = None
        if self.api_key:
            self._init_service()

    def _init_service(self):
        """Initialize Google API client service."""
        try:
            from googleapiclient.discovery import build
            self._service = build("youtube", "v3", developerKey=self.api_key)
            logger.info("YouTube Data API v3 client successfully initialized.")
        except Exception as e:
            logger.warning(f"Could not initialize YouTube Data API client: {e}")
            self._service = None

    def analyze_channel(
        self,
        identifier: str,
        max_videos: int = 100,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Tuple[YouTubeChannel, List[YouTubeVideo]]:
        """
        Analyze a YouTube channel by identifier (@handle, Channel ID UC..., or URL).
        Returns YouTubeChannel and list of detailed YouTubeVideo objects.
        """
        if not self._service:
            logger.info("No YouTube API key provided or service unavailable; using fallback extractor.")
            fallback = YouTubeFallbackExtractor()
            return fallback.extract_channel_and_videos(identifier, max_videos=max_videos)

        try:
            channel_id = self.resolve_channel_id(identifier)
            if not channel_id:
                raise ValueError(f"Could not resolve channel ID for: {identifier}")

            channel = self.get_channel_profile(channel_id)
            if progress_callback:
                progress_callback(10, 100, f"Found channel: {channel.title}")

            videos = self.fetch_channel_videos(
                channel, max_videos=max_videos, progress_callback=progress_callback
            )
            channel.videos = videos
            return channel, videos

        except Exception as e:
            logger.warning(f"YouTube Data API query failed ({e}). Attempting fallback extraction...")
            fallback = YouTubeFallbackExtractor()
            return fallback.extract_channel_and_videos(identifier, max_videos=max_videos)

    def resolve_channel_id(self, identifier: str) -> Optional[str]:
        """
        Resolve channel ID from handle (@username), channel ID (UC...),
        custom name, or full channel URL.
        """
        cleaned = identifier.strip()

        # Handle full URL
        if "youtube.com" in cleaned or "youtu.be" in cleaned:
            # Match channel/UC...
            m_channel = re.search(r"youtube\.com/channel/(UC[\w-]{22})", cleaned)
            if m_channel:
                return m_channel.group(1)
            # Match @handle
            m_handle = re.search(r"youtube\.com/@([\w.-]+)", cleaned)
            if m_handle:
                cleaned = f"@{m_handle.group(1)}"
            # Match c/username or user/username
            m_user = re.search(r"youtube\.com/(?:c|user)/([\w.-]+)", cleaned)
            if m_user:
                cleaned = m_user.group(1)

        # Directly a UC ID
        if cleaned.startswith("UC") and len(cleaned) == 24:
            return cleaned

        # Handle (@handle)
        handle_query = cleaned if cleaned.startswith("@") else f"@{cleaned}"
        try:
            req = self._service.channels().list(
                part="id,snippet",
                forHandle=handle_query,
            )
            resp = req.execute()
            items = resp.get("items", [])
            if items:
                return items[0]["id"]
        except Exception as e:
            logger.debug(f"forHandle query failed: {e}")

        # Search for channel by query
        try:
            req = self._service.search().list(
                part="snippet",
                q=cleaned.lstrip("@"),
                type="channel",
                maxResults=1,
            )
            resp = req.execute()
            items = resp.get("items", [])
            if items:
                return items[0]["snippet"]["channelId"]
        except Exception as e:
            logger.debug(f"Search by query failed: {e}")

        return None

    def get_channel_profile(self, channel_id: str) -> YouTubeChannel:
        """Fetch channel metadata, statistics, and uploads playlist ID."""
        req = self._service.channels().list(
            part="snippet,statistics,contentDetails,brandingSettings",
            id=channel_id,
        )
        resp = req.execute()
        items = resp.get("items", [])
        if not items:
            raise ValueError(f"Channel not found for ID: {channel_id}")

        item = items[0]
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        content_details = item.get("contentDetails", {})
        branding = item.get("brandingSettings", {})

        uploads_id = content_details.get("relatedPlaylists", {}).get("uploads")

        channel = YouTubeChannel(
            channel_id=channel_id,
            title=snippet.get("title", ""),
            custom_url=snippet.get("customUrl", ""),
            description=snippet.get("description", ""),
            published_at=format_datetime(snippet.get("publishedAt", "")),
            subscriber_count=safe_int(stats.get("subscriberCount")),
            video_count=safe_int(stats.get("videoCount")),
            view_count=safe_int(stats.get("viewCount")),
            country=snippet.get("country"),
            avatar_url=snippet.get("thumbnails", {}).get("high", {}).get("url"),
            banner_url=branding.get("image", {}).get("bannerExternalUrl"),
            uploads_playlist_id=uploads_id,
        )
        return channel

    def fetch_channel_videos(
        self,
        channel: YouTubeChannel,
        max_videos: int = 100,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[YouTubeVideo]:
        """
        Fetch up to max_videos from the channel's uploads playlist.
        Batches calls in 50s for maximum performance.
        """
        if not channel.uploads_playlist_id:
            logger.warning("No uploads playlist ID found for channel.")
            return []

        video_ids: List[str] = []
        next_page_token = None

        logger.info(f"Fetching up to {max_videos} video IDs from playlist {channel.uploads_playlist_id}...")

        while len(video_ids) < max_videos:
            fetch_count = min(50, max_videos - len(video_ids))
            req = self._service.playlistItems().list(
                part="contentDetails",
                playlistId=channel.uploads_playlist_id,
                maxResults=fetch_count,
                pageToken=next_page_token,
            )
            resp = req.execute()

            for item in resp.get("items", []):
                v_id = item.get("contentDetails", {}).get("videoId")
                if v_id and v_id not in video_ids:
                    video_ids.append(v_id)

            next_page_token = resp.get("nextPageToken")
            if not next_page_token:
                break

            if progress_callback:
                progress_callback(
                    min(40, int(len(video_ids) / max_videos * 40)),
                    100,
                    f"Retrieved {len(video_ids)} video references...",
                )

        logger.info(f"Retrieved {len(video_ids)} video IDs. Fetching detailed statistics...")
        videos = self._fetch_video_details_batch(video_ids, progress_callback)
        return videos

    def _fetch_video_details_batch(
        self,
        video_ids: List[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[YouTubeVideo]:
        """Batch query video details (duration, view count, likes, comments)."""
        videos: List[YouTubeVideo] = []
        batch_size = 50

        for i in range(0, len(video_ids), batch_size):
            chunk = video_ids[i : i + batch_size]
            req = self._service.videos().list(
                part="snippet,contentDetails,statistics",
                id=",".join(chunk),
            )
            resp = req.execute()

            for item in resp.get("items", []):
                v_id = item.get("id")
                snippet = item.get("snippet", {})
                content_details = item.get("contentDetails", {})
                stats = item.get("statistics", {})

                iso_duration = content_details.get("duration", "")
                duration_secs = parse_iso_duration(iso_duration)
                formatted_duration = format_duration(duration_secs)

                is_short = (
                    duration_secs <= Config.SHORTS_THRESHOLD_SECONDS and duration_secs > 0
                )
                if "#shorts" in snippet.get("title", "").lower():
                    is_short = True

                thumbnails = snippet.get("thumbnails", {})
                thumb_url = (
                    thumbnails.get("high", {}).get("url")
                    or thumbnails.get("default", {}).get("url")
                    or f"https://i.ytimg.com/vi/{v_id}/hqdefault.jpg"
                )

                video = YouTubeVideo(
                    video_id=v_id,
                    title=snippet.get("title", "Untitled"),
                    description=snippet.get("description", "")[:500],
                    published_at=format_datetime(snippet.get("publishedAt", "")),
                    duration_seconds=duration_secs,
                    duration_formatted=formatted_duration,
                    is_short=is_short,
                    view_count=safe_int(stats.get("viewCount")),
                    like_count=safe_int(stats.get("likeCount")),
                    comment_count=safe_int(stats.get("commentCount")),
                    url=f"https://www.youtube.com/watch?v={v_id}",
                    thumbnail_url=thumb_url,
                )
                videos.append(video)

            if progress_callback:
                pct = 40 + int(len(videos) / max(1, len(video_ids)) * 55)
                progress_callback(pct, 100, f"Analyzed {len(videos)} of {len(video_ids)} videos...")

        return videos
