import os
import time
import json
import io
from pathlib import Path
from dotenv import load_dotenv

import streamlit as st
from fpdf import FPDF

from summerizer import UniversalSummarizer
from src.utils import detect_source_type, SourceType, clean_url

# Page config
st.set_page_config(
    page_title="Universal Content Summarizer",
    page_icon="[S]",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
<style>
    .main { padding: 0rem 1rem; }
    .summary-box {
        background-color: #f0f9ff;
        border-radius: 10px;
        padding: 20px;
        border-left: 5px solid #0284c7;
        color: #000000;
    }
    .insight-box {
        background-color: #f0fdf4;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #16a34a;
        color: #000000;
    }
    .topic-tag {
        display: inline-block;
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 4px 10px;
        border-radius: 15px;
        margin: 3px;
        font-size: 0.85em;
        font-weight: bold;
    }
    .meta-info {
        background-color: #f8fafc;
        border-radius: 8px;
        padding: 12px;
        border: 1px solid #e2e8f0;
        color: #000000;
        font-size: 0.85em;
    }
</style>
""", unsafe_allow_html=True)


# Title
st.title("Universal Content Summarizer")
st.markdown(
    "### Summarize any website, YouTube video, PDF or text instantly"
)
st.markdown("---")


# Sidebar
with st.sidebar:
    st.header("Settings")

    # API Key
    st.subheader("Groq API Key")
    api_key_input = st.text_input(
        "Enter API key",
        type="password",
        placeholder="gsk_...",
        help="Get free key at https://console.groq.com/keys"
    )

    # Load from .env if not provided
    if not api_key_input:
        load_dotenv()
        env_key = os.getenv("GROQ_API_KEY", "")
        if env_key and env_key != "your_groq_api_key_here":
            api_key_input = env_key
            st.success("API key loaded from .env")
    else:
        st.success("API key set")

    if api_key_input:
        os.environ["GROQ_API_KEY"] = api_key_input

    st.markdown("---")

    # Summary settings
    st.subheader("Summary Options")

    summary_style = st.selectbox(
        "Summary Style",
        options=[
            "detailed",
            "brief",
            "bullet_points",
            "academic",
            "simple"
        ],
        index=0,
        help=(
            "detailed: Full summary\n"
            "brief: 2-3 sentences\n"
            "bullet_points: Key points list\n"
            "academic: Formal style\n"
            "simple: Easy to understand"
        )
    )

    st.subheader("Extract")
    extract_insights = st.checkbox("Key Insights", value=True)
    extract_topics = st.checkbox("Main Topics", value=True)

    st.markdown("---")

    st.subheader("Supported Sources")
    st.markdown("""
    - Any website URL
    - YouTube videos
    - PDF files (upload)
    - Direct text paste
    - Wikipedia articles
    - News articles
    - Research papers
    - Blog posts
    """)

    st.markdown("---")
    st.markdown("Powered by Groq + LLaMA3")


# Initialize summarizer
@st.cache_resource
def get_summarizer(api_key: str) -> UniversalSummarizer:
    return UniversalSummarizer(
        groq_api_key=api_key,
        model="openai/gpt-oss-120b"
    )


# Helper: Export to PDF
def create_pdf_export(result: dict) -> bytes:
    """Create PDF export of summary"""

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 16)

    # Title
    title = result.get('title', 'Summary')[:80]
    pdf.cell(0, 10, title, ln=True)
    pdf.ln(5)

    # Source info
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 8, f"Source: {result.get('source_type', 'unknown').upper()}", ln=True)
    if result.get('url'):
        url_text = result['url'][:80]
        pdf.cell(0, 8, f"URL: {url_text}", ln=True)
    pdf.cell(
        0, 8,
        f"Style: {result.get('style', 'detailed').replace('_', ' ').title()}",
        ln=True
    )
    pdf.ln(5)

    # Summary
    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(0, 10, "Summary", ln=True)
    pdf.set_font('Helvetica', '', 11)

    summary = result.get('summary', 'No summary available')
    summary_lines = summary.split('\n')
    for line in summary_lines:
        if line.strip():
            pdf.multi_cell(0, 7, line.strip())

    pdf.ln(5)

    # Key Insights
    if result.get('insights'):
        pdf.set_font('Helvetica', 'B', 13)
        pdf.cell(0, 10, "Key Insights", ln=True)
        pdf.set_font('Helvetica', '', 11)
        insights_lines = result['insights'].split('\n')
        for line in insights_lines:
            if line.strip():
                pdf.multi_cell(0, 7, line.strip())
        pdf.ln(5)

    # Topics
    if result.get('topics'):
        pdf.set_font('Helvetica', 'B', 13)
        pdf.cell(0, 10, "Main Topics", ln=True)
        pdf.set_font('Helvetica', '', 11)
        topics_text = ", ".join(result['topics'])
        pdf.multi_cell(0, 7, topics_text)

    return bytes(pdf.output())


# Helper: Display result
def display_result(result: dict):
    """Display summarization result"""

    # Metadata card
    source_type = result.get('source_type', 'unknown').upper()
    title = result.get('title', 'Unknown')
    proc_time = result.get('processing_time', 0)

    st.markdown(
        f"""<div class='meta-info'>
        <strong>Source:</strong> {source_type} |
        <strong>Title:</strong> {title[:80]} |
        <strong>Words:</strong> {result.get('word_count', 0):,} |
        <strong>Processing:</strong> {proc_time:.1f}s
        </div>""",
        unsafe_allow_html=True
    )

    # YouTube specific info
    if result.get('source_type') == 'youtube':
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(
                "Duration", f"{result.get('duration_minutes', 0)} min"
            )
        with c2:
            views = result.get('views', 0)
            views_str = (
                f"{views/1_000_000:.1f}M" if views > 1_000_000
                else f"{views/1_000:.0f}K" if views > 1_000
                else str(views)
            )
            st.metric("Views", views_str)
        with c3:
            st.metric("Channel", result.get('author', 'Unknown')[:20])

    st.markdown("---")

    # Summary
    st.subheader("Summary")
    st.markdown(
        f"""<div class='summary-box'>
        <span style='color:#000000;'>{result.get('summary', '')}</span>
        </div>""",
        unsafe_allow_html=True
    )

    # Insights and Topics
    if result.get('insights') or result.get('topics'):
        col1, col2 = st.columns(2)

        with col1:
            if result.get('insights'):
                st.subheader("Key Insights")
                st.markdown(
                    f"""<div class='insight-box'>
                    <span style='color:#000000;'>
                    {result.get('insights', '')}
                    </span>
                    </div>""",
                    unsafe_allow_html=True
                )

        with col2:
            if result.get('topics'):
                st.subheader("Main Topics")
                topics_html = ""
                for topic in result['topics']:
                    topics_html += (
                        f"<span class='topic-tag'>{topic}</span>"
                    )
                st.markdown(topics_html, unsafe_allow_html=True)

    st.markdown("---")

    # Export options
    st.subheader("Export Summary")
    export_col1, export_col2 = st.columns(2)

    with export_col1:
        # Export as text
        export_text = f"""SUMMARY - {result.get('title', 'Content')}
Source: {result.get('source_type', 'unknown').upper()}
URL: {result.get('url', 'N/A')}
Style: {result.get('style', 'detailed')}

SUMMARY:
{result.get('summary', '')}

KEY INSIGHTS:
{result.get('insights', 'N/A')}

MAIN TOPICS:
{', '.join(result.get('topics', []))}
"""
        st.download_button(
            label="Download as TXT",
            data=export_text,
            file_name="summary.txt",
            mime="text/plain",
            use_container_width=True
        )

    with export_col2:
        # Export as PDF
        try:
            pdf_bytes = create_pdf_export(result)
            st.download_button(
                label="Download as PDF",
                data=pdf_bytes,
                file_name="summary.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.caption(f"PDF export unavailable: {str(e)[:50]}")

    # Copy as JSON
    with st.expander("View Raw JSON"):
        st.json(result)


# Main tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "URL Summarizer",
    "Text Summarizer",
    "PDF Summarizer",
    "History"
])


# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []


# Tab 1: URL Summarizer
with tab1:
    st.header("Summarize from URL")
    st.markdown(
        "Paste any URL - website, YouTube video, "
        "article or Wikipedia page."
    )

    # Example URLs
    with st.expander("Example URLs to try"):
        examples = [
            "https://en.wikipedia.org/wiki/Artificial_intelligence",
            "https://en.wikipedia.org/wiki/Machine_learning",
            "https://www.youtube.com/watch?v=aircAruvnKk",
            "https://www.youtube.com/watch?v=PaCmpygFfXo",
            "https://towardsdatascience.com/..."
        ]
        for ex in examples:
            st.code(ex)

    url_input = st.text_input(
        "Enter URL:",
        placeholder=(
            "https://www.youtube.com/watch?v=... "
            "or https://any-website.com/article"
        )
    )

    # Detect source type preview
    if url_input.strip():
        cleaned = clean_url(url_input)
        source_type = detect_source_type(cleaned)
        type_labels = {
            SourceType.YOUTUBE: "YouTube Video",
            SourceType.WEBSITE: "Website/Article",
            SourceType.TEXT: "Text",
            SourceType.UNKNOWN: "Unknown - may not work"
        }
        st.caption(
            f"Detected: {type_labels.get(source_type, 'Unknown')}"
        )

    summarize_url_btn = st.button(
        "Summarize URL",
        type="primary",
        use_container_width=False
    )

    if summarize_url_btn:
        if not api_key_input:
            st.error("Please enter your Groq API key in the sidebar!")
        elif not url_input.strip():
            st.warning("Please enter a URL!")
        else:
            with st.spinner(
                "Extracting content and generating summary..."
            ):
                try:
                    summarizer = get_summarizer(api_key_input)

                    result = summarizer.summarize_url(
                        url=url_input.strip(),
                        style=summary_style,
                        extract_insights=extract_insights,
                        extract_topics=extract_topics
                    )

                    st.session_state.history.append(result)
                    st.success("Summary generated successfully!")
                    display_result(result)

                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.info(
                        "Tips:\n"
                        "- Make sure the URL is accessible\n"
                        "- YouTube videos need captions enabled\n"
                        "- Some websites block scraping"
                    )


# Tab 2: Text Summarizer
with tab2:
    st.header("Summarize Text")
    st.markdown("Paste any text directly to get an instant summary.")

    text_title = st.text_input(
        "Title (optional):",
        placeholder="Give your text a title"
    )

    text_input = st.text_area(
        "Paste your text here:",
        height=300,
        placeholder=(
            "Paste any text here - articles, notes, "
            "research, documents..."
        )
    )

    if text_input:
        word_count = len(text_input.split())
        char_count = len(text_input)
        st.caption(
            f"Words: {word_count:,} | Characters: {char_count:,}"
        )

    summarize_text_btn = st.button(
        "Summarize Text",
        type="primary"
    )

    if summarize_text_btn:
        if not api_key_input:
            st.error("Please enter your Groq API key!")
        elif len(text_input.strip()) < 50:
            st.warning("Please enter at least 50 characters of text!")
        else:
            with st.spinner("Generating summary..."):
                try:
                    summarizer = get_summarizer(api_key_input)

                    result = summarizer.summarize_text_direct(
                        text=text_input,
                        style=summary_style,
                        title=text_title or "Custom Text"
                    )

                    st.session_state.history.append(result)
                    st.success("Summary generated!")
                    display_result(result)

                except Exception as e:
                    st.error(f"Error: {str(e)}")


# Tab 3: PDF Summarizer
with tab3:
    st.header("Summarize PDF")
    st.markdown(
        "Upload any PDF file to get an AI-powered summary."
    )

    uploaded_pdf = st.file_uploader(
        "Upload PDF file",
        type=["pdf"],
        help="Maximum file size: 50MB"
    )

    if uploaded_pdf:
        file_size_mb = uploaded_pdf.size / (1024 * 1024)
        st.info(
            f"File: **{uploaded_pdf.name}** "
            f"({file_size_mb:.1f} MB)"
        )

        summarize_pdf_btn = st.button(
            "Summarize PDF",
            type="primary"
        )

        if summarize_pdf_btn:
            if not api_key_input:
                st.error("Please enter your Groq API key!")
            else:
                with st.spinner(
                    "Extracting text and generating summary..."
                ):
                    try:
                        summarizer = get_summarizer(api_key_input)
                        pdf_bytes = uploaded_pdf.read()

                        result = summarizer.summarize_pdf(
                            pdf_bytes=pdf_bytes,
                            style=summary_style
                        )

                        st.session_state.history.append(result)
                        st.success("PDF summarized successfully!")
                        display_result(result)

                    except Exception as e:
                        st.error(f"Error: {str(e)}")


# Tab 4: History
with tab4:
    st.header("Summary History")

    if not st.session_state.history:
        st.info("No summaries yet. Start summarizing content!")
    else:
        # Summary stats
        history = st.session_state.history
        total = len(history)
        youtube_count = sum(
            1 for h in history if h.get('source_type') == 'youtube'
        )
        web_count = sum(
            1 for h in history if h.get('source_type') == 'website'
        )
        pdf_count = sum(
            1 for h in history if h.get('source_type') == 'pdf'
        )
        text_count = sum(
            1 for h in history if h.get('source_type') == 'text'
        )
        avg_time = sum(
            h.get('processing_time', 0) for h in history
        ) / total

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric("Total", total)
        with c2:
            st.metric("YouTube", youtube_count)
        with c3:
            st.metric("Websites", web_count)
        with c4:
            st.metric("PDFs", pdf_count)
        with c5:
            st.metric("Avg Time", f"{avg_time:.1f}s")

        st.markdown("---")

        # Clear history
        if st.button("Clear History", type="secondary"):
            st.session_state.history = []
            st.rerun()

        # Show each summary
        for i, result in enumerate(reversed(history)):
            title = result.get('title', 'Unknown')[:60]
            source = result.get('source_type', 'unknown').upper()

            with st.expander(
                f"#{total-i} [{source}] {title}"
            ):
                st.markdown(f"**Summary:**")
                st.write(result.get('summary', ''))

                if result.get('url'):
                    st.markdown(f"**URL:** {result['url']}")

                if result.get('topics'):
                    topics_str = " | ".join(result['topics'])
                    st.caption(f"Topics: {topics_str}")

                proc_time = result.get('processing_time', 0)
                words = result.get('word_count', 0)
                st.caption(
                    f"Processed in {proc_time:.1f}s | "
                    f"{words:,} words"
                )


# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Universal Content Summarizer |
    Groq + LLaMA3 + Streamlit</p>
    <p style='font-size: 12px;'>
    Supports: Websites, YouTube, PDFs, Text
    </p>
</div>
""", unsafe_allow_html=True)