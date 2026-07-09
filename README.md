# SummarizeAI - Universal Content Summarizer

A full-stack AI-powered web application that summarizes any content
from websites, YouTube videos, PDFs, or plain text using Groq's
ultra-fast LLM inference.

---

## Live Demo

https://universal-summerizer-hfiwzcv56bbmkx6otaxwrz.streamlit.app/

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [Supported Sources](#supported-sources)
- [Summary Styles](#summary-styles)
- [Deployment](#deployment)
- [Screenshots](#screenshots)
- [Limitations](#limitations)
- [Future Improvements](#future-improvements)
- [License](#license)
- [Contact](#contact)

---

## Overview

SummarizeAI is a production-ready full-stack web application that
leverages large language models to instantly summarize any type of
content. Instead of spending hours reading articles, watching long
videos, or going through lengthy documents, users can get accurate
AI-generated summaries in seconds.

The application uses a React frontend with a FastAPI Python backend,
with Groq's API providing ultra-fast LLM inference using the
openai/gpt-oss-120b model.

Use Cases:
- Researchers summarizing academic papers quickly
- Students getting key points from lecture materials
- Professionals digesting long industry reports
- Content creators understanding competitor content
- Anyone who needs to process information faster

---

## Features

### Content Sources
- Any website or article URL
- YouTube videos via transcript extraction
- PDF file upload and parsing
- Direct text paste

### AI Capabilities
- Five summary styles (brief, detailed, bullet points, academic, simple)
- Key insights extraction
- Main topic identification and tagging
- Long content chunking and combining

### User Experience
- Real-time loading with animated spinner
- Summary history with session stats
- Copy to clipboard with one click
- Download summary as TXT file
- Drag and drop PDF upload
- Mobile responsive design
- Example URLs for quick testing

### Technical
- FastAPI REST backend with full OpenAPI docs
- React frontend with Tailwind CSS
- Docker containerization for both services
- CORS configured for development and production
- Proper error handling and user feedback

---

## Tech Stack

### Backend

| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.10 | Core language |
| FastAPI | 0.104.1 | REST API framework |
| Uvicorn | 0.24.0 | ASGI server |
| Groq | 0.9.0 | LLM inference API |
| newspaper3k | 0.2.8 | Article extraction |
| BeautifulSoup4 | 4.12.2 | HTML parsing |
| youtube-transcript-api | 0.6.2 | YouTube transcripts |
| PyPDF | 3.17.1 | PDF text extraction |
| LangChain | 0.2.16 | LLM orchestration |
| Pydantic | 2.4.2 | Data validation |


### Infrastructure

| Technology | Purpose |
|-----------|---------|
| Docker | Containerization |
| Docker Compose | Multi-service orchestration |
| Groq API | LLM inference (free tier available) |

---

## Architecture

User Browser
|
v
React Frontend (Port 5173)
|
| HTTP requests (Axios)
v
FastAPI Backend (Port 8000)
|
|-- Website URL --> newspaper3k + BeautifulSoup
|-- YouTube URL --> YouTube Transcript API
|-- PDF Upload  --> PyPDF
|-- Direct Text --> Text Cleaner
|
v
Text Cleaning + Chunking (LangChain)
|
v
Groq API (openai/gpt-oss-120b)
|
v
Summary + Insights + Topics
|
v
JSON Response to Frontend
|
v
Display Result + Update History


### Content Extraction Pipeline
Input URL/File/Text
|
v
Source Detection (YouTube / Website / PDF / Text)
|
|
|     |     |
v     v     v
YouTube  Web   PDF
Trans-  Scrape Parse
cript   (BS4 + (PyPDF)
API     news)
|     |     |
|||
|
v
Text Cleaning
(remove noise, normalize)
|
v
Chunking (4000 chars, 200 overlap)
|
|
|           |
Short       Long
(<4000)   (>4000)
|           |
v           v
Direct    Chunk +
Summary   Combine
|
v
Final Summary
|
|
|      |      |
v      v      v
Sum-  Key    Topic
mary  Insights Tags

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Groq API key (free at https://console.groq.com/keys)
- Docker (optional, for containerized setup)

### Installation

#### Method 1: Manual Setup (Development)

Step 1: Clone the repository

```bash
git clone https://github.com/yourusername/summarize-ai.git
cd summarize-ai
```

Step 2: Setup backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

Step 3: Setup frontend

```bash
cd ../frontend

# Install dependencies
npm install

# Create .env file
echo "VITE_API_URL=http://localhost:8000" > .env
```

Step 4: Run both services

```bash
# Terminal 1 - Backend
cd backend
uvicorn main:app --reload --port 8000


Step 5: Open in browser

http://localhost:5173

#### Method 2: Docker Compose (Recommended)

Step 1: Clone and configure

```bash
git clone https://github.com/yourusername/summarize-ai.git
cd summarize-ai
```

Step 2: Create root .env file

```bash
echo "GROQ_API_KEY=your_key_here" > .env
```

Step 3: Start all services

```bash
docker-compose up --build
```

Step 4: Open in browser

http://localhost:5173

### Getting Your Groq API Key

1. Go to https://console.groq.com/keys
2. Create a free account
3. Click Create API Key
4. Copy the key
5. Add it to your .env file or paste it in the app sidebar

The free tier provides generous usage limits suitable for
personal and development use.

---
---

## API Reference

The backend exposes a REST API with the following endpoints.

Full interactive documentation is available at:

http://localhost:8000/docs

### GET /api/health

Check if the API and summarizer are running.

Response:
```json
{
  "status": "healthy",
  "summarizer_ready": true,
  "model": "openai/gpt-oss-120b"
}
```

### POST /api/summarize/url

Summarize content from a website or YouTube URL.

Request body:
```json
{
  "url": "https://www.youtube.com/watch?v=aircAruvnKk",
  "style": "detailed"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "url": "https://www.youtube.com/watch?v=aircAruvnKk",
    "source_type": "youtube",
    "source_name": "YouTube Video",
    "title": "But what is a neural network?",
    "summary": "...",
    "insights": "...",
    "topics": ["neural networks", "deep learning", "AI"],
    "style": "detailed",
    "word_count": 8432,
    "char_count": 45123,
    "processing_time": 12.4,
    "truncated": false,
    "duration_minutes": 19,
    "author": "3Blue1Brown",
    "views": 14500000,
    "thumbnail_url": "https://..."
  }
}
```

### POST /api/summarize/text

Summarize directly pasted text.

Request body:
```json
{
  "text": "Your long text content here...",
  "title": "My Article",
  "style": "bullet_points"
}
```

### POST /api/summarize/pdf

Summarize an uploaded PDF file.

Request: multipart/form-data with:
- file: PDF file (max 50MB)
- style: Summary style string

---

## Supported Sources

### Websites and Articles

Any publicly accessible website works including:
- News articles (BBC, CNN, TechCrunch, etc.)
- Wikipedia pages
- Blog posts and Medium articles
- Documentation pages
- Research paper landing pages

Note: Some websites block automated access. In these cases
the extraction may fail and a helpful error message is shown.

### YouTube Videos

Requirements for YouTube summarization:
- The video must have captions or auto-generated subtitles enabled
- The video must be publicly accessible (not private or unlisted)
- Both standard and Shorts URLs are supported

Supported URL formats:

https://www.youtube.com/watch?v=VIDEO_ID
https://youtu.be/VIDEO_ID
https://youtube.com/shorts/VIDEO_ID
https://www.youtube.com/embed/VIDEO_ID

### PDF Files

- Maximum file size: 50MB
- Must contain extractable text (not scanned images)
- Both text-based and mixed PDFs are supported
- Supports multi-page documents

### Direct Text

- Minimum 50 characters required
- No maximum length (very long texts are chunked automatically)
- Supports any language (summary will match content language)

---

## Summary Styles

| Style | Description | Best For |
|-------|-------------|---------|
| Detailed | Full comprehensive summary in paragraphs | Research, in-depth understanding |
| Brief | 2-3 sentence overview | Quick overview, skimming |
| Bullet Points | Key points as organized bullets | Presentations, notes |
| Academic | Formal style with objective and findings | Research papers, reports |
| Simple | Plain language without jargon | Sharing with non-experts |

---

## Deployment

### Backend - Render

1. Go to https://render.com
2. Create new Web Service from GitHub
3. Set root directory to backend/
4. Build command: pip install -r requirements.txt
5. Start command: uvicorn main:app --host 0.0.0.0 --port $PORT
6. Add environment variable: GROQ_API_KEY=your_key

### Full Stack - Docker on Any VPS

```bash
# On your server
git clone your-repo
cd summarize-ai
echo "GROQ_API_KEY=your_key" > .env
docker-compose up -d --build
```

---

## Limitations

### Technical Limitations

1. YouTube videos without captions cannot be summarized
2. Websites that block automated requests may fail
3. Scanned PDF images cannot be processed (text-only)
4. Very long content is truncated at 50,000 characters
5. Processing time depends on content length (10-60 seconds)

### API Limitations

1. Groq free tier has rate limits (check console.groq.com)
2. Context window limits apply to very long documents
3. Summary quality depends on source content quality

### Language Support

The app works best with English content. Other languages
may work but are not officially tested or guaranteed.

---

## Future Improvements

### Short Term
- User authentication and persistent history
- Database storage for summaries
- Additional export formats (PDF, Markdown)
- Batch URL processing
- Custom prompt templates

### Medium Term
- Browser extension for one-click summarization
- Email digest feature
- API key management UI
- Webhook support for automated pipelines
- Multiple LLM provider support

### Long Term
- Multimodal support (images in articles)
- Audio file transcription and summarization
- Integration with note-taking apps
- Team collaboration features
- Custom fine-tuned summarization model

---

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature/your-feature-name
```

3. Make your changes following the existing code style
4. Test your changes locally
5. Commit with a clear message

```bash
git commit -m "Add: your feature description"
```

6. Push and open a Pull Request

### Code Style

Backend:
- Follow PEP 8 for Python code
- Use type hints for all functions
- Add docstrings to public functions
- Handle all exceptions explicitly

Frontend:
- Use functional components with hooks
- Keep components focused and reusable
- Use Tailwind utility classes
- Avoid inline styles

---

## License

MIT License

Copyright (c) 2024 Adhiraj Chakravorty

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

---

## Contact

Adhiraj Chakravorty

- Email: youradhi20@gmail.com
- LinkedIn: https://www.linkedin.com/in/adhiraj-chakravorty-788685344/
- GitHub: https://github.com/ADHIRAJ994

### Project Links

- Repository: https://github.com/ADHIRAJ994/summarize-ai
- Live Demo: https://universal-summerizer-hfiwzcv56bbmkx6otaxwrz.streamlit.app/
- Issues: https://github.com/ADHIRAJ994/summarize-ai/issues

---

## Acknowledgments

- Groq for providing ultra-fast LLM inference API
- newspaper3k for excellent article extraction
- YouTube Transcript API for caption extraction
- The FastAPI team for the excellent framework
- The React team for the UI library
- Tailwind CSS for the utility-first styling approach

---

Built with React, FastAPI and Groq