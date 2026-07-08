import os
import time
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

from src.web_extractor import extract_website_content
from src.youtube_extractor import extract_youtube_content
from src.pdf_extractor import extract_pdf_content
from src.text_cleaner import clean_text, split_into_chunks
from src.utils import detect_source_type, SourceType, clean_url

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Summary style prompts
SUMMARY_PROMPTS = {
    "brief": """Provide a brief summary of the following content in 2-3 
    sentences. Focus on the most important points only.
    
    Content: {content}
    
    Brief Summary:""",

    "detailed": """Provide a comprehensive and detailed summary of the 
    following content. Include all main points, key arguments, important 
    details and conclusions. Write in clear paragraphs.
    
    Content: {content}
    
    Detailed Summary:""",

    "bullet_points": """Summarize the following content as clear bullet points.
    Include:
    - Main topic (1 line)
    - Key points (5-8 bullets)
    - Important conclusions (2-3 bullets)
    
    Content: {content}
    
    Bullet Point Summary:""",

    "academic": """Provide an academic-style summary of the following content.
    Include: objective/purpose, methodology (if applicable), main findings,
    conclusions and implications. Use formal language.
    
    Content: {content}
    
    Academic Summary:""",

    "simple": """Explain the following content in very simple terms that a 
    12-year-old could understand. Avoid technical jargon and use plain 
    everyday language.
    
    Content: {content}
    
    Simple Explanation:"""
}

# Combined summary prompt for long content
COMBINE_PROMPT = """You have been given multiple partial summaries of a 
longer piece of content. Combine them into one coherent, well-structured 
final summary. Remove repetition and ensure smooth flow.

Partial Summaries:
{summaries}

Final Combined Summary:"""

# Key insights extraction prompt
INSIGHTS_PROMPT = """Extract the top 5 most important insights or takeaways 
from the following content. Each insight should be actionable or memorable.
Format as a numbered list.

Content: {content}

Top 5 Key Insights:"""

# Topic extraction prompt
TOPICS_PROMPT = """Identify the main topics and themes discussed in the 
following content. List them as comma-separated keywords (maximum 10 topics).

Content: {content}

Main Topics:"""


class UniversalSummarizer:
    """
    Universal content summarizer supporting multiple source types
    """

    def __init__(
        self,
        groq_api_key: str,
        model: str = "openai/gpt-oss-120b",
        temperature: float = 0.1,
        max_tokens: int = 2048
    ):
        self.client = Groq(api_key=groq_api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        logger.info(f"Summarizer initialized with model: {model}")

    def _call_llm(self, prompt: str) -> str:
        """Make a single LLM call"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert content summarizer. "
                            "You create clear, accurate and useful summaries."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def summarize_text(
        self,
        text: str,
        style: str = "detailed",
        chunk_size: int = 4000
    ) -> str:
        """
        Summarize text content
        Handles long content by chunking and combining
        """

        # Clean text
        text = clean_text(text)

        # Split into chunks if needed
        chunks = split_into_chunks(text, chunk_size=chunk_size)

        if len(chunks) == 1:
            # Short content - summarize directly
            prompt = SUMMARY_PROMPTS[style].format(content=chunks[0])
            return self._call_llm(prompt)

        else:
            # Long content - summarize each chunk then combine
            logger.info(f"Processing {len(chunks)} chunks...")

            chunk_summaries = []
            for i, chunk in enumerate(chunks):
                logger.info(f"Summarizing chunk {i+1}/{len(chunks)}")
                prompt = SUMMARY_PROMPTS["brief"].format(content=chunk)
                chunk_summary = self._call_llm(prompt)
                chunk_summaries.append(chunk_summary)
                time.sleep(0.5)  # Rate limiting

            # Combine summaries
            combined_summaries = '\n\n'.join([
                f"Part {i+1}: {s}"
                for i, s in enumerate(chunk_summaries)
            ])

            combine_prompt = COMBINE_PROMPT.format(
                summaries=combined_summaries
            )

            return self._call_llm(combine_prompt)

    def extract_insights(self, text: str) -> str:
        """Extract key insights from content"""

        # Use first 4000 chars for insights
        truncated = text[:4000] if len(text) > 4000 else text
        prompt = INSIGHTS_PROMPT.format(content=truncated)
        return self._call_llm(prompt)

    def extract_topics(self, text: str) -> List[str]:
        """Extract main topics from content"""

        truncated = text[:2000] if len(text) > 2000 else text
        prompt = TOPICS_PROMPT.format(content=truncated)
        topics_str = self._call_llm(prompt)

        # Parse comma-separated topics
        topics = [t.strip() for t in topics_str.split(',')]
        topics = [t for t in topics if t and len(t) > 2]

        return topics[:10]

    def summarize_url(
        self,
        url: str,
        style: str = "detailed",
        extract_insights: bool = True,
        extract_topics: bool = True
    ) -> Dict:
        """
        Main function - summarize content from any URL
        """

        start_time = time.time()
        url = clean_url(url)

        # Detect source type
        source_type = detect_source_type(url)
        logger.info(f"Source type: {source_type.value}")

        # Extract content based on source
        if source_type == SourceType.YOUTUBE:
            content_data = extract_youtube_content(url)
            source_name = "YouTube Video"

        elif source_type == SourceType.WEBSITE:
            content_data = extract_website_content(url)
            source_name = "Website"

        else:
            raise ValueError(
                f"Unsupported URL type. "
                f"Please use a YouTube or website URL."
            )

        text = content_data.get('text', '')

        if not text or len(text) < 50:
            raise ValueError("Could not extract meaningful content from URL")

        # Generate summary
        logger.info(f"Generating {style} summary...")
        summary = self.summarize_text(text, style=style)

        # Extract insights if requested
        insights = None
        if extract_insights:
            logger.info("Extracting key insights...")
            insights = self.extract_insights(text)

        # Extract topics if requested
        topics = None
        if extract_topics:
            logger.info("Extracting topics...")
            topics = self.extract_topics(text)

        processing_time = time.time() - start_time

        result = {
            'url': url,
            'source_type': source_type.value,
            'source_name': source_name,
            'title': content_data.get('title', 'Unknown'),
            'summary': summary,
            'insights': insights,
            'topics': topics,
            'style': style,
            'word_count': content_data.get('word_count', 0),
            'char_count': content_data.get('char_count', 0),
            'processing_time': processing_time,
            'truncated': content_data.get('truncated', False)
        }

        # Add source-specific metadata
        if source_type == SourceType.YOUTUBE:
            result['duration_minutes'] = content_data.get(
                'duration_minutes', 0
            )
            result['author'] = content_data.get('author', '')
            result['views'] = content_data.get('views', 0)
            result['thumbnail_url'] = content_data.get('thumbnail_url', '')

        return result

    def summarize_text_direct(
        self,
        text: str,
        style: str = "detailed",
        title: str = "Custom Text"
    ) -> Dict:
        """
        Summarize directly pasted text
        """

        start_time = time.time()

        if len(text) < 50:
            raise ValueError("Text too short to summarize")

        summary = self.summarize_text(text, style=style)
        insights = self.extract_insights(text)
        topics = self.extract_topics(text)

        processing_time = time.time() - start_time

        return {
            'url': None,
            'source_type': 'text',
            'source_name': 'Direct Text',
            'title': title,
            'summary': summary,
            'insights': insights,
            'topics': topics,
            'style': style,
            'word_count': len(text.split()),
            'char_count': len(text),
            'processing_time': processing_time,
            'truncated': False
        }

    def summarize_pdf(
        self,
        pdf_bytes: bytes,
        style: str = "detailed"
    ) -> Dict:
        """
        Summarize PDF file content
        """

        start_time = time.time()

        content_data = extract_pdf_content(pdf_bytes)
        text = content_data.get('text', '')

        if not text or len(text) < 50:
            raise ValueError("No extractable text found in PDF")

        summary = self.summarize_text(text, style=style)
        insights = self.extract_insights(text)
        topics = self.extract_topics(text)

        processing_time = time.time() - start_time

        return {
            'url': None,
            'source_type': 'pdf',
            'source_name': 'PDF Document',
            'title': content_data.get('title', 'PDF Document'),
            'author': content_data.get('author', ''),
            'num_pages': content_data.get('num_pages', 0),
            'summary': summary,
            'insights': insights,
            'topics': topics,
            'style': style,
            'word_count': content_data.get('word_count', 0),
            'char_count': content_data.get('char_count', 0),
            'processing_time': processing_time,
            'truncated': content_data.get('truncated', False)
        }