from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class YouTubeVideo:
    """Represents a single YouTube video and its OSINT metadata."""
    video_id: str
    title: str
    description: str
    published_at: str
    duration_seconds: int
    duration_formatted: str
    is_short: bool
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    url: str = ""
    thumbnail_url: str = ""

    def __post_init__(self):
        if not self.url and self.video_id:
            self.url = f"https://www.youtube.com/watch?v={self.video_id}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class YouTubeChannel:
    """Represents a YouTube Channel profile and its aggregated metrics."""
    channel_id: str
    title: str
    custom_url: str
    description: str
    published_at: str
    subscriber_count: int
    video_count: int
    view_count: int
    country: Optional[str] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    uploads_playlist_id: Optional[str] = None
    videos: List[YouTubeVideo] = field(default_factory=list)

    def to_dict(self, include_videos: bool = True) -> Dict[str, Any]:
        res = asdict(self)
        if not include_videos:
            res.pop("videos", None)
        return res
