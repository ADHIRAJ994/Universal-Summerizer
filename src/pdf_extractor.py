import pypdf
import io
from typing import Dict,Union
import logging

logger = logging.getLogger(__name__)

def extract_pdf_content(pdf_source:Union[str,bytes,io.BytesIO])->Dict:
    """
    Extract text content from PDF file

    Args:
        pdf_source: File path, bytes, or BytesIO object
    """

    try:
        # Handle different input types
        if isinstance(pdf_source, str):
            reader = pypdf.PdfReader(pdf_source)
        elif isinstance(pdf_source, bytes):
            reader = pypdf.PdfReader(io.BytesIO(pdf_source))
        else:
            reader = pypdf.PdfReader(pdf_source)

        metadata = reader.metadata or {}
        title = metadata.get('/Title', 'Unknown PDF')
        author = metadata.get('/Author', 'Unknown Author')
        num_pages = len(reader.pages)

        pages_text = []
        for page_num, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    pages_text.append(page_text.strip())
            except Exception as e:
                logger.warning(f"Error extracting page {page_num+1}: {e}")

        if not pages_text:
            raise ValueError("No text content found in PDF")
        
        full_text = '\n\n'.join(pages_text)

        # Clean text
        lines = full_text.split('\n')
        clean_lines = [line.strip() for line in lines if len(line.strip()) > 10]
        clean_text = '\n'.join(clean_lines)

        max_length = 50000
        truncated = False
        if len(clean_text) > max_length:
            clean_text = clean_text[:max_length]
            truncated = True

        return {
            'title': str(title),
            'author': str(author),
            'num_pages': num_pages,
            'text': clean_text,
            'char_count': len(clean_text),
            'word_count': len(clean_text.split()),
            'truncated': truncated,
            'source': 'pdf'
        }
    
    except Exception as e:
        raise ValueError(f"Failed to extract PDF content: {str(e)}")
    

