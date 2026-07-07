import re
from typing import str as String

def clean_text(text:str)->str:
    """
    Clean and normalize extracted text
    """

    # Remove multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Remove multiple spaces
    text = re.sub(r' {2,}', ' ', text)

    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\"\'\n]', ' ', text)

    lines = text.split('\n')
    clean_lines = [
        line.strip() for line in lines
        if len(line.strip()) > 20
    ]

    text = '\n'.join(clean_lines)

    return text.strip()


def split_into_chunks(text:str,chunk_size:int=4000,chunk_overlap:int=200)->list:
    """
    Split text into overlapping chunks for processing
    """

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end < len(text):
            # Find last period before end
            last_period = text.rfind('.', start, end)
            if last_period > start + chunk_size // 2:
                end = last_period + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - chunk_overlap

    return chunks

def truncate_text(text: str, max_words: int = 10000) -> str:
    """Truncate text to maximum word count"""

    words = text.split()
    if len(words) <= max_words:
        return text

    return ' '.join(words[:max_words]) + '...'