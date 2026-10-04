from collections import Counter
from datetime import datetime
from statistics import mean
from typing import Any, Dict, List, Optional
import pandas as pd
from ..instagram.models import InstagramPost, InstagramProfile


class InstagramProfileAnalyzer:
    """
    Analytics engine for Instagram OSINT metrics:
    Post type distribution, engagement rates, and top posts.
    """

    def __init__(self, profile: InstagramProfile, posts: Optional[List[InstagramPost]] = None):
        self.profile = profile
        self.posts = posts or profile.posts
        self._df: Optional[pd.DataFrame] = None

    @property
    def dataframe(self) -> pd.DataFrame:
        if self._df is None:
            data = [p.to_dict() for p in self.posts]
            if not data:
                self._df = pd.DataFrame(
                    columns=[
                        "post_id", "shortcode", "post_type", "published_at",
                        "caption", "like_count", "comment_count",
                        "video_duration_seconds", "url",
                    ]
                )
            else:
                df = pd.DataFrame(data)
                df["like_count"] = pd.to_numeric(df["like_count"], errors="coerce").fillna(0).astype(int)
                df["comment_count"] = pd.to_numeric(df["comment_count"], errors="coerce").fillna(0).astype(int)
                self._df = df
        return self._df

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Compute aggregate metrics for Instagram profile and recent posts."""
        df = self.dataframe
        total_posts = len(df)

        type_counts = Counter(df["post_type"].tolist()) if not df.empty else Counter()
        photos_count = type_counts.get("Photo", 0)
        videos_count = type_counts.get("Video", 0)
        reels_count = type_counts.get("Reel", 0)
        carousels_count = type_counts.get("Carousel", 0)

        total_likes = int(df["like_count"].sum()) if not df.empty else 0
        total_comments = int(df["comment_count"].sum()) if not df.empty else 0
        avg_likes = int(df["like_count"].mean()) if not df.empty else 0
        avg_comments = int(df["comment_count"].mean()) if not df.empty else 0

        # Engagement rate per post relative to followers
        followers = max(1, self.profile.follower_count)
        engagement_rate = round(((avg_likes + avg_comments) / followers) * 100, 2) if followers > 0 else 0.0

        return {
            "username": self.profile.username,
            "full_name": self.profile.full_name,
            "followers": self.profile.follower_count,
            "following": self.profile.following_count,
            "total_profile_posts": self.profile.total_posts,
            "analyzed_posts_count": total_posts,
            "photos_count": photos_count,
            "videos_count": videos_count,
            "reels_count": reels_count,
            "carousels_count": carousels_count,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "avg_likes_per_post": avg_likes,
            "avg_comments_per_post": avg_comments,
            "engagement_rate_pct": engagement_rate,
            "is_verified": self.profile.is_verified,
            "is_private": self.profile.is_private,
        }

    def get_top_posts_by_likes(self, limit: int = 10) -> pd.DataFrame:
        df = self.dataframe
        if df.empty:
            return df
        return df.sort_values(by="like_count", ascending=False).head(limit)
