import re
from datetime import datetime, timezone
from typing import Any, Optional


def safe_int(value: Any, default: int = 0) -> int:
    """Safely converts input to integer."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def parse_iso_duration(iso_str: Optional[str]) -> int:
    """
    Parse an ISO 8601 duration string (e.g. 'PT1H15M33S', 'PT45S', 'PT2M')
    into total duration in seconds.
    Supports isodate library with robust regex fallback.
    """
    if not iso_str:
        return 0

    try:
        import isodate
        parsed = isodate.parse_duration(iso_str)
        return int(parsed.total_seconds())
    except Exception:
        pass

    # Regex fallback for ISO 8601: P[nD]T[nH][nM][nS]
    pattern = r"P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?"
    match = re.match(pattern, iso_str)
    if not match:
        return 0

    parts = match.groupdict()
    days = safe_int(parts.get("days"))
    hours = safe_int(parts.get("hours"))
    minutes = safe_int(parts.get("minutes"))
    seconds = safe_int(parts.get("seconds"))

    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def format_duration(seconds: int) -> str:
    """
    Format seconds into readable HH:MM:SS or MM:SS format.
    Example: 85 -> '01:25', 3665 -> '01:01:05'
    """
    if not seconds or seconds < 0:
        return "00:00"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_number(val: Any) -> str:
    """
    Format large integers into readable metrics like 1.5M, 24.2K.
    """
    num = safe_int(val)
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f}B"
    if num >= 1_000_000:
        return f"{num / 1_000_000:.2f}M"
    if num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return f"{num:,}"


def format_datetime(val: Any) -> str:
    """Format datetime string or object into standard YYYY-MM-DD HH:MM."""
    if not val:
        return "N/A"
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d %H:%M")
    if isinstance(val, str):
        try:
            # Handle ISO format strings like '2023-08-15T12:00:00Z'
            cleaned = val.replace("Z", "+00:00")
            dt = datetime.fromisoformat(cleaned)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return val[:16] if len(val) >= 16 else val
    return str(val)
