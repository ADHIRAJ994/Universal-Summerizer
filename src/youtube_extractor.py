from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import re
from typing import Dict,Optional,List
import logging

logger = logging.getLogger(__name__)

def extract_video_id(url:str)->Optional[str]:
    """
    Extract YouTube video ID from various URL formats

    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://youtube.com/shorts/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    """
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:shorts\/)([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None

def get_video_metadata(video_id: str) -> Dict:
    """Get basic video metadata using pytube"""

    try:
        from pytube import YouTube

        yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")

        return {
            'title': yt.title,
            'author': yt.author,
            'length_seconds': yt.length,
            'views': yt.views,
            'description': yt.description[:500] if yt.description else '',
            'thumbnail_url': yt.thumbnail_url
        }
    
    except Exception as e:
        logger.warning(f"Could not get video metadata: {e}")

        return {
            'title': f'YouTube Video ({video_id})',
            'author': 'Unknown',
            'length_seconds': 0,
            'views': 0,
            'description': '',
            'thumbnail_url': ''
        }
    
def get_transcript(
    video_id: str,
    languages: List[str] = ['en', 'en-US', 'en-GB']
) -> Optional[str]:
    """
    Get transcript for a YouTube video

    Falls back to auto-generated captions if manual not available
    """
    try:
        # Try to get transcript in preferred languages
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        transcript = None

        # Try manual transcripts first
        try:
            transcript = transcript_list.find_manually_created_transcript(
                languages
            )
        except Exception:
            pass

        if transcript is None:
            try:
                transcript = transcript_list.find_generated_transcript(
                    languages
                )
            except Exception:
                pass

        if transcript is None:
            for t in transcript_list:
                transcript = t
                break

        if transcript is None:
            return None
        
        transcript_data = transcript.fetch()
        formatter = TextFormatter()
        text = formatter.format_transcript(transcript_data)

        return text
    
    except Exception as e:
        logger.error(f"Failed to get transcript: {e}")
        return None
    
def extract_youtube_content(url: str) -> Dict:
    """
    Main YouTube content extraction function
    """

    video_id = extract_video_id(url)

    if video_id is None:
        raise ValueError(
            f"Could not extract video ID from URL: {url}\n"
            "Please provide a valid YouTube URL."
        )
    
    # Get metadata
    metadata = get_video_metadata(video_id)

    # Get transcript
    transcript = get_transcript(video_id)

    if transcript is None:
        raise ValueError(
            f"No transcript available for video: {metadata['title']}\n"
            "The video may not have captions enabled."
        )
    
    # Clean transcript
    lines = transcript.split('\n')
    clean_lines = [line.strip() for line in lines if line.strip()]
    clean_transcript = ' '.join(clean_lines)

    # Truncate if too long
    max_length = 50000
    truncated = False
    if len(clean_transcript) > max_length:
        clean_transcript = clean_transcript[:max_length]
        truncated = True

    duration_mins = metadata['length_seconds'] // 60


    return {
        'title': metadata['title'],
        'author': metadata['author'],
        'duration_minutes': duration_mins,
        'views': metadata['views'],
        'description': metadata['description'],
        'thumbnail_url': metadata['thumbnail_url'],
        'transcript': clean_transcript,
        'text': clean_transcript,
        'char_count': len(clean_transcript),
        'word_count': len(clean_transcript.split()),
        'truncated': truncated,
        'video_id': video_id,
        'url': url,
        'source': 'youtube'
    }
