import os
import logging
from typing import Optional
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from summerizer import UniversalSummarizer

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
summarizer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global summarizer

    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY not found")
    else:
        summarizer = UniversalSummarizer(
            groq_api_key=GROQ_API_KEY,
            model="openai/gpt-oss-120b"
        )
        logger.info("Summarizer initialized")

    yield
    logger.info("Shutting down")


app = FastAPI(
    title="Universal Content Summarizer API",
    description=(
        "Summarize any URL, YouTube video, PDF or text "
        "using AI. Supports multiple summary styles."
    ),
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class URLRequest(BaseModel):
    url: str
    style: str = "detailed"
    extract_insights: bool = True
    extract_topics: bool = True


class TextRequest(BaseModel):
    text: str
    title: str = "Custom Text"
    style: str = "detailed"


@app.get("/", tags=["General"])
def root():
    return {
        "name": "Universal Content Summarizer API",
        "version": "1.0.0",
        "supported_sources": [
            "YouTube URLs",
            "Any website URL",
            "PDF files",
            "Direct text"
        ],
        "supported_styles": [
            "brief",
            "detailed",
            "bullet_points",
            "academic",
            "simple"
        ]
    }


@app.get("/health", tags=["General"])
def health():
    return {
        "status": "healthy",
        "summarizer_ready": summarizer is not None
    }


@app.post("/summarize/url", tags=["Summarize"])
def summarize_url(request: URLRequest):
    if summarizer is None:
        raise HTTPException(
            status_code=503,
            detail="Summarizer not initialized. Check API key."
        )

    if not request.url.strip():
        raise HTTPException(
            status_code=400,
            detail="URL cannot be empty"
        )

    try:
        result = summarizer.summarize_url(
            url=request.url,
            style=request.style,
            extract_insights=request.extract_insights,
            extract_topics=request.extract_topics
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Summarization failed: {str(e)}"
        )


@app.post("/summarize/text", tags=["Summarize"])
def summarize_text(request: TextRequest):
    if summarizer is None:
        raise HTTPException(status_code=503, detail="Not initialized")

    if len(request.text.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Text too short. Minimum 50 characters."
        )

    try:
        result = summarizer.summarize_text_direct(
            text=request.text,
            style=request.style,
            title=request.title
        )
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Summarization failed: {str(e)}"
        )


@app.post("/summarize/pdf", tags=["Summarize"])
async def summarize_pdf(
    file: UploadFile = File(...),
    style: str = "detailed"
):
    if summarizer is None:
        raise HTTPException(status_code=503, detail="Not initialized")

    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    try:
        pdf_bytes = await file.read()

        if len(pdf_bytes) > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="PDF too large. Maximum 50MB."
            )

        result = summarizer.summarize_pdf(
            pdf_bytes=pdf_bytes,
            style=style
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF summarization failed: {str(e)}"
        )