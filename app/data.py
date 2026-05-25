from .models import Project
from typing import cast
from pydantic import HttpUrl

PROJECTS = [
    Project(
        slug="llm-assistant",
        title="AI-Powered Document Assistant with RAG",
        description="Production-ready Retrieval-Augmented Generation (RAG) system with multi-format document parsing (PDF, DOCX, CSV with link extraction), intelligent semantic chunking, and vector search using Qdrant. Features Azure OpenAI integration with conversation history, content filtering, adaptive garbage collection, and API monitoring with performance alerts. Built with async Quart backend, multiple embedding providers (SentenceTransformers, Azure, FastEmbed), and comprehensive lifecycle management.",
        technologies=["Python", "Quart", "Qdrant", "Azure OpenAI", "RAG", "Vector Search", "NLP"],
        repo_url=cast(HttpUrl,"https://github.com/Ajollyworld79/llm-assistant")
    ),

    Project(
        slug="document-intelligence-pipeline",
        title="Document Intelligence Pipeline",
        description=(
            "Local document processing pipeline for PDF, DOCX and scanned images: OCR (Tesseract), text extraction, "
            "table detection & extraction, key-value parsing, entity recognition (spaCy), layout analysis and summarization. "
            "Results are produced as structured JSON suitable for downstream ingestion (data lakes, BI, search indexes). "
            "Repository is private — contact guch79@gmail.com for access and commercial options."
        ),
        technologies=["Python", "Quart", "OCR", "Tesseract", "spaCy", "PDF processing", "NLP"],
        repo_url=cast(HttpUrl,"https://github.com/Ajollyworld79/document-intelligence-pipeline"),
        live_url=cast(HttpUrl,"https://document-intelligence-pipeline-production.up.railway.app")
    ),

    Project(
        slug="personal-project",
        title="Professional Portfolio & CV Generator",
        description="Fully asynchronous Quart web application with auto-generated PDF CV from dynamic content. Features intelligent HTML-to-PDF conversion with structured data extraction, professional formatting, and clickable links. Built with modern async Python patterns.",
        technologies=["Quart", "Uvicorn", "FPDF2", "Async Python", "Jinja2"],
        repo_url=cast(HttpUrl,"https://github.com/Ajollyworld79/personal-project")
    ),
    Project(
        slug="apology-service",
        title="Apology-as-a-Service (MCP Server)",
        description="A live Model Context Protocol (MCP) server that provides context-aware crisis communication for AI agents. Test it live right here with the 'Generate Live Apology' button, or <a href='/static/mcp-config.json' target='_blank' style='color:#f2849e;'>download the config</a> to connect your own agent. Features multiple severity levels, styles (including Haiku), and SSE support.",
        technologies=["Python", "MCP Protocol", "SSE", "Docker", "Async", "FastMCP"],
        repo_url=cast(HttpUrl, "https://github.com/Ajollyworld79/Apology-as-a-Service"),
        live_url=cast(HttpUrl, "https://apology-as-a-service-production.up.railway.app/sse")
    ),
    Project(
        slug="data-pipeline",
        title="ETL Data Pipeline - Dataverse to SQL Server",
        description="Complete ETL pipeline for extracting data from Microsoft Dataverse, transforming with business logic, and loading to SQL Server. Includes fake data generation with Faker for testing before production deployment. Features parallel processing, connection pooling, and circuit breakers.",
        technologies=["Python", "Pandas", "SQLAlchemy", "Dataverse", "Faker"],
        repo_url=cast(HttpUrl,"https://github.com/Ajollyworld79/data-pipeline")
    ),

    Project(
        slug="the-cold-file",
        title="The Cold File — Autonomous AI YouTube Channel",
        description=(
            "Production Python backend that fully operates a YouTube channel — "
            "<a href='https://www.youtube.com/@The_Cold_File' target='_blank' rel='noopener noreferrer' style='color:#f2849e;'>@The_Cold_File</a> — "
            "with Claude wearing multiple intelligent hats across a single 30,000-line pipeline. "
            "<br><br>"
            "<strong>Claude is not just the writer.</strong> Opus generates concepts and 10,000–11,000-word horror or fictional true-crime scripts across 17 horror archetypes and 14 case types. "
            "A separate Sonnet pass is the <em>quality gate</em>: it scores N parallel candidate concepts against a weighted rubric (hook 35%, retention 30%, etc.) — only the winner enters production, losers are logged for prompt-tuning. "
            "Sonnet then plays <em>casting director</em>: it reads tone, narrative voice, and protagonist profile, and picks both the Azure Dragon HD voice <em>and</em> the inference parameter string (temperature/top_p/cfg_scale) that matches the story's emotional register — measured dread vs. clinical vs. frantic. "
            "Claude also authors every per-scene Flux 2 Pro image prompt, gated through atmosphere maps and safety clauses (no recognizable faces on fictional true-crime imagery). "
            "<br><br>"
            "<strong>Real-world signal in, abstracted prompt fuel out.</strong> A topical-signal miner pulls Google Trends + NewsAPI headlines, then Claude distills them into structural <em>beat shapes</em> (e.g. \"DNA match decades later\") — never leaking real case names into the fictional show. "
            "A title miner analyzes competitor channels for winning title structures. "
            "A YouTube Analytics feedback loop produces weekly insights that feed back into concept generation. "
            "<br><br>"
            "<strong>13+ Postgres tables</strong> track everything: <code>stories</code>, <code>concept_candidates</code>, <code>cold_open_attempts</code>, <code>video_performance</code>, <code>weekly_insights</code>, <code>title_patterns</code>, <code>recurring_characters</code>, <code>topical_signals</code>, <code>comment_interactions</code>, <code>schedule</code>, plus dedup history that prevents repeating concepts or titles across horror and true-crime modes. "
            "FFmpeg compiles 1080p video; YouTube Data API v3 handles uploads, Shorts trailers, and chapter markers. "
            "Runs hourly on Railway. Three production modes (<code>season</code>, <code>single</code>, <code>truecrime</code>) selectable via env var."
        ),
        technologies=["Python", "Claude Opus", "Claude Sonnet", "Azure OpenAI", "Azure Flux", "Azure Speech", "FFmpeg", "PostgreSQL", "YouTube API", "NewsAPI", "Railway"],
        live_url=cast(HttpUrl, "https://www.youtube.com/@The_Cold_File"),
    ),

]
