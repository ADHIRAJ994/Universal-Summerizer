import validators
import re
from enum import Enum


class SourceType(Enum):
    YOUTUBE = "youtube"
    WEBSITE = "website"
    PDF = "pdf"
    TEXT = "text"
    UNKNOWN = "unknown"


def detect_source_type(url_or_text: str) -> SourceType:
    """
    Detect the type of content source
    """

    text = url_or_text.strip()

    # Check if YouTube
    youtube_patterns = [
        r'youtube\.com/watch',
        r'youtu\.be/',
        r'youtube\.com/shorts/',
        r'youtube\.com/embed/'
    ]

    for pattern in youtube_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return SourceType.YOUTUBE

    # Check if valid URL
    if validators.url(text):
        return SourceType.WEBSITE

    # Check if it's plain text (not URL)
    if len(text) > 100 and not text.startswith('http'):
        return SourceType.TEXT

    return SourceType.UNKNOWN


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable string"""

    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}m {secs}s"
    else:
        hours = seconds // 3600
        mins = (seconds % 3600) // 60
        return f"{hours}h {mins}m"


def format_number(n: int) -> str:
    """Format large numbers with K/M suffixes"""

    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def clean_url(url: str) -> str:
    """Clean and normalize URL"""

    url = url.strip()

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    return url