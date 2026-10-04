import re
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
import requests
from ..config import Config
from ..utils.formatters import format_datetime, safe_int
from ..utils.logger import setup_logger
from .models import InstagramPost, InstagramProfile

logger = setup_logger("instagram_client")


class InstagramOSINTClient:
    """
    Instagram OSINT Client for extracting profile metrics and post metadata.
    Supports instaloader and anonymous web queries.
    """

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.auth_username = username or Config.INSTAGRAM_USERNAME
        self.auth_password = password or Config.INSTAGRAM_PASSWORD
        self._loader = None

    def _get_loader(self):
        """Lazily initialize Instaloader instance."""
        if self._loader is None:
            try:
                import instaloader
                self._loader = instaloader.Instaloader(
                    download_pictures=False,
                    download_videos=False,
                    download_video_thumbnails=False,
                    download_geotags=False,
                    download_comments=False,
                    save_metadata=False,
                    quiet=True,
                )
                if self.auth_username and self.auth_password:
                    try:
                        self._loader.login(self.auth_username, self.auth_password)
                        logger.info(f"Logged into Instagram as {self.auth_username}")
                    except Exception as e:
                        logger.warning(f"Instagram login failed: {e}. Proceeding anonymously.")
            except ImportError:
                logger.warning("Instaloader not installed. Falling back to HTTP public meta extractor.")
                self._loader = None
        return self._loader

    def analyze_profile(
        self,
        identifier: str,
        max_posts: int = 30,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Tuple[InstagramProfile, List[InstagramPost]]:
        """
        Analyze an Instagram profile by username or profile URL.
        """
        username = self._clean_username(identifier)
        loader = self._get_loader()

        if loader:
            try:
                return self._analyze_with_instaloader(username, max_posts, progress_callback)
            except Exception as e:
                logger.warning(f"Instaloader query failed for {username}: {e}. Trying HTTP public fallback...")

        return self._analyze_with_http_fallback(username)

    def _analyze_with_instaloader(
        self,
        username: str,
        max_posts: int,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Tuple[InstagramProfile, List[InstagramPost]]:
        """Extract profile and posts using Instaloader."""
        import instaloader

        profile_obj = instaloader.Profile.from_username(self._loader.context, username)

        profile = InstagramProfile(
            username=profile_obj.username,
            full_name=profile_obj.full_name or "",
            biography=profile_obj.biography or "",
            external_url=profile_obj.external_url,
            follower_count=profile_obj.followers,
            following_count=profile_obj.followees,
            total_posts=profile_obj.mediacount,
            is_verified=profile_obj.is_verified,
            is_private=profile_obj.is_private,
            is_business_account=profile_obj.is_business_account,
            profile_pic_url=profile_obj.profile_pic_url,
        )

        posts: List[InstagramPost] = []
        if profile.is_private and not profile_obj.followed_by_viewer:
            logger.info(f"Profile {username} is private. Cannot extract posts.")
            return profile, posts

        if progress_callback:
            progress_callback(20, 100, f"Found profile: @{username}. Extracting posts...")

        count = 0
        for p in profile_obj.get_posts():
            if count >= max_posts:
                break

            post_type = "Photo"
            duration = None
            if p.is_video:
                post_type = "Reel" if p.video_view_count is not None else "Video"
                duration = safe_int(p.video_duration) if hasattr(p, "video_duration") else None
            elif hasattr(p, "typename") and p.typename == "GraphSidecar":
                post_type = "Carousel"

            post = InstagramPost(
                post_id=str(p.mediaid),
                shortcode=p.shortcode,
                post_type=post_type,
                published_at=format_datetime(p.date_utc),
                caption=(p.caption or "")[:300],
                like_count=safe_int(p.likes),
                comment_count=safe_int(p.comments),
                video_duration_seconds=duration,
                url=f"https://www.instagram.com/p/{p.shortcode}/",
                thumbnail_url=p.url,
            )
            posts.append(post)
            count += 1

            if progress_callback and count % 5 == 0:
                progress_callback(
                    20 + int((count / max_posts) * 75),
                    100,
                    f"Analyzed {count} posts...",
                )

        profile.posts = posts
        return profile, posts

    def _analyze_with_http_fallback(self, username: str) -> Tuple[InstagramProfile, List[InstagramPost]]:
        """
        Lightweight HTTP public fallback: queries Instagram public page headers
        to extract basic details (followers, following, posts count).
        """
        url = f"https://www.instagram.com/{username}/"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

        resp = requests.get(url, headers=headers, timeout=10)
        html = resp.text

        # Extract meta description: "X Followers, Y Following, Z Posts - See Instagram photos and videos from..."
        meta_match = re.search(
            r'<meta\s+name="description"\s+content="([^"]*)"',
            html,
            re.IGNORECASE,
        )

        followers, following, posts_count = 0, 0, 0
        bio = ""
        full_name = username

        if meta_match:
            desc_content = meta_match.group(1)
            # Parse stats e.g. "10M Followers, 150 Following, 1,230 Posts"
            stat_match = re.search(
                r"([\d.,KMkm]+)\s+Followers,\s+([\d.,KMkm]+)\s+Following,\s+([\d.,KMkm]+)\s+Posts",
                desc_content,
            )
            if stat_match:
                followers = self._parse_compact_number(stat_match.group(1))
                following = self._parse_compact_number(stat_match.group(2))
                posts_count = self._parse_compact_number(stat_match.group(3))

        # Title contains name
        title_match = re.search(r"<title>([^<]*)</title>", html, re.IGNORECASE)
        if title_match:
            t_text = title_match.group(1)
            if "•" in t_text:
                full_name = t_text.split("•")[0].strip()

        profile = InstagramProfile(
            username=username,
            full_name=full_name,
            biography=bio,
            external_url=None,
            follower_count=followers,
            following_count=following,
            total_posts=posts_count,
            is_verified=False,
            is_private=False,
            is_business_account=False,
            posts=[],
        )
        return profile, []

    def _clean_username(self, identifier: str) -> str:
        """Strip URL prefix and @ symbol."""
        cleaned = identifier.strip().rstrip("/")
        if "instagram.com" in cleaned:
            parts = cleaned.split("instagram.com/")
            if len(parts) > 1:
                cleaned = parts[1].split("/")[0].split("?")[0]
        cleaned = cleaned.lstrip("@")
        return cleaned

    def _parse_compact_number(self, val_str: str) -> int:
        """Convert '10.5K', '2.3M', '1,234' string to integer."""
        val_str = val_str.replace(",", "").strip().upper()
        try:
            if "M" in val_str:
                return int(float(val_str.replace("M", "")) * 1_000_000)
            if "K" in val_str:
                return int(float(val_str.replace("K", "")) * 1_000)
            return int(float(val_str))
        except Exception:
            return 0
