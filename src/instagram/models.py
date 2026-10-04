from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class InstagramPost:
    """Represents a single Instagram post and its OSINT metadata."""
    post_id: str
    shortcode: str
    post_type: str  # 'Photo', 'Video', 'Reel', 'Carousel'
    published_at: str
    caption: str
    like_count: int = 0
    comment_count: int = 0
    video_duration_seconds: Optional[int] = None
    url: str = ""
    thumbnail_url: str = ""

    def __post_init__(self):
        if not self.url and self.shortcode:
            self.url = f"https://www.instagram.com/p/{self.shortcode}/"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InstagramProfile:
    """Represents an Instagram Profile and aggregated metrics."""
    username: str
    full_name: str
    biography: str
    external_url: Optional[str]
    follower_count: int
    following_count: int
    total_posts: int
    is_verified: bool
    is_private: bool
    is_business_account: bool
    profile_pic_url: Optional[str] = None
    posts: List[InstagramPost] = field(default_factory=list)

    def to_dict(self, include_posts: bool = True) -> Dict[str, Any]:
        res = asdict(self)
        if not include_posts:
            res.pop("posts", None)
        return res
