import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables from .env file if present
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()


class Config:
    """Application configuration management."""

    # API Keys & Credentials
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "").strip()
    INSTAGRAM_USERNAME: str = os.getenv("INSTAGRAM_USERNAME", "").strip()
    INSTAGRAM_PASSWORD: str = os.getenv("INSTAGRAM_PASSWORD", "").strip()

    # Default scrapers and limits
    DEFAULT_MAX_VIDEOS: int = int(os.getenv("DEFAULT_MAX_VIDEOS", "200"))
    OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", str(DATA_DIR)))

    # Short video threshold (in seconds)
    # YouTube Shorts are vertical videos 60 seconds or less
    SHORTS_THRESHOLD_SECONDS: int = 60

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def set_youtube_api_key(cls, key: str) -> None:
        """Dynamically update YouTube API key during runtime."""
        cls.YOUTUBE_API_KEY = key.strip()

    @classmethod
    def has_youtube_api_key(cls) -> bool:
        """Check if a valid YouTube API key is configured."""
        return bool(cls.YOUTUBE_API_KEY)
