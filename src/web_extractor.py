import requests
from bs4 import BeautifulSoup
import html2text
from newspaper import Article
from typing import Dict,Optional
import logging

logger = logging.getLogger(__name__)

def extract_with_newspaper(url:str)->Optional[Dict]:
    """Extraact article content using newspaper4k
    Best for news articles and blogs"""
    try:
        article = Article(url)
        article.download()
        article.parse()
        article.nlp()

        if not article.text or len(article.text)<100:
            return None
        
        return{
            'title':article.title or 'Unknown Title',
            'text':article.text,
            'authors':article.authors,
            'publish_date':str(article.publish_date) if article.publish_date else None,
            'top_image': article.top_image,
            'keywords': article.keywords,
            'summary': article.summary,
            'source': 'newspaper4k'
        }
    except Exception as e:
        logger.warning(f"Newspaper Extraction failed: {e}")
        return None
    
def extract_with_beautifulsoup(url:str,timeout:int = 30)->Optional[Dict]:
    """
    Extract content using BeautifulSoup
    Works for most websites
    """
    try:
        headers = {
            'User-Agent':(
                'Mozilla/5.0(Windows NT 10.0;Win64;x64)'
                'AppleWebKit/537.36(KHTML NT,like Gecko)'
                'Chrome/120.0.0.0 Safari/537.36'
            )
        }
        response = requests.get(url,headers=headers,timeout=timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.content,'lxml')

        for tag in soup(['script','style','nav','header',
                         'footer','aside','advertisement',
                         'cookie','popup']):
            tag.decompose()



        title = ' '
        if soup.tile:
            title = soup.title.string or ''

        elif soup.find('h1'):
            title = soup.find('h1').get_text(strip=True)

        meta_desc = ''
        meta_tag = soup.find('meta', attrs={'name': 'description'})
        if meta_tag:
            meta_desc = meta_tag.get('content', '')


        content_selectors = [
            'article',
            'main',
            '.content',
            '.article-body',
            '.post-content',
            '.entry-content',
            '#content',
            '#main'
        ]

        main_content = None
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                main_content = element
                break

        if main_content is None:
            main_content = soup.find('body')

        if main_content is None:
            return None
        

        converter = html2text.HTML2Text()
        converter.ignore_links = True
        converter.ignore_images = True
        converter.ignore_emphasis = False
        converter.body_width = 0

        text = converter.handle(str(main_content))

        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line and len(line) > 30]
        clean_text = '\n'.join(lines)

        if len(clean_text) < 100:
            return None

        return {
            'title': title.strip(),
            'text': clean_text,
            'meta_description': meta_desc,
            'source': 'beautifulsoup',
            'url': url
        }
    
    except Exception as e:
        logger.error(f"BeautifulSoup extraction failed: {e}")
        return None
    

def extract_website_content(url: str) -> Dict:
    """
    Main website content extraction function
    Tries multiple methods for best results
    """

    result = None

    # Try newspaper4k first (best for articles)
    result = extract_with_newspaper(url)

    if result is None:
        result = extract_with_beautifulsoup(url)

    if result is None:
        raise ValueError(
            f"Could not extract content from URL: {url}\n"
            "The website may be blocking scraping or require JavaScript."
        )
    
    max_length = 50000
    if len(result['text']) > max_length:
        result['text'] = result['text'][:max_length]
        result['truncated'] = True
    else:
        result['truncated'] = False

    result['char_count'] = len(result['text'])
    result['word_count'] = len(result['text'].split())

    return result