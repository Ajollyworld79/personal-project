from .models import Project
from typing import cast
from pydantic import HttpUrl

PROJECTS = [
    Project(
        slug="llm-assistant",
        title="AI-Powered Document Assistant with RAG",
        description=(
            "Production-ready Retrieval-Augmented Generation (RAG) system with multi-format document parsing (PDF, DOCX, CSV with link extraction), intelligent semantic chunking, and vector search using Qdrant."
            "<!--more-->"
            "Features Azure OpenAI integration with conversation history, content filtering, adaptive garbage collection, and API monitoring with performance alerts. Built with async Quart backend, multiple embedding providers (SentenceTransformers, Azure, FastEmbed), and comprehensive lifecycle management."
        ),
        technologies=["Python", "Quart", "Qdrant", "Azure OpenAI", "RAG", "Vector Search", "NLP"],
        repo_url=cast(HttpUrl,"https://github.com/Ajollyworld79/llm-assistant")
    ),

    Project(
        slug="document-intelligence-pipeline",
        title="Document Intelligence Pipeline",
        description=(
            "Local document processing pipeline for PDF, DOCX and scanned images: OCR (Tesseract), text extraction, "
            "table detection & extraction, key-value parsing, entity recognition (spaCy), layout analysis and summarization."
            "<!--more-->"
            "Results are produced as structured JSON suitable for downstream ingestion (data lakes, BI, search indexes). "
            "Repository is private — contact guch79@gmail.com for access and commercial options."
        ),
        technologies=["Python", "Quart", "OCR", "Tesseract", "spaCy", "PDF processing", "NLP"],
        live_url=cast(HttpUrl,"https://document-intelligence-pipeline-production.up.railway.app")
    ),

    Project(
        slug="personal-project",
        title="Professional Portfolio & CV Generator",
        description=(
            "Fully asynchronous Quart web application with auto-generated PDF CV from dynamic content."
            "<!--more-->"
            "Features intelligent HTML-to-PDF conversion with structured data extraction, professional formatting, and clickable links. Built with modern async Python patterns."
        ),
        technologies=["Quart", "Uvicorn", "FPDF2", "Async Python", "Jinja2"],
        repo_url=cast(HttpUrl,"https://github.com/Ajollyworld79/personal-project")
    ),
    Project(
        slug="apology-service",
        title="Apology-as-a-Service (MCP Server)",
        description=(
            "A live Model Context Protocol (MCP) server that provides context-aware crisis communication for AI agents."
            "<!--more-->"
            "Test it live right here with the 'Generate Live Apology' button, or "
            "<a href='/static/mcp-config.json' target='_blank' rel='noopener noreferrer' style='color:#f2849e;'>download the config</a> "
            "to connect your own agent. Features multiple severity levels, styles (including Haiku), and SSE support."
        ),
        technologies=["Python", "MCP Protocol", "SSE", "Docker", "Async", "FastMCP"],
        repo_url=cast(HttpUrl, "https://github.com/Ajollyworld79/Apology-as-a-Service"),
        live_url=cast(HttpUrl, "https://apology-as-a-service-production.up.railway.app/sse")
    ),
    Project(
        slug="data-pipeline",
        title="ETL Data Pipeline - Dataverse to SQL Server",
        description=(
            "Complete ETL pipeline for extracting data from Microsoft Dataverse, transforming with business logic, and loading to SQL Server."
            "<!--more-->"
            "Includes fake data generation with Faker for testing before production deployment. Features parallel processing, connection pooling, and circuit breakers."
        ),
        technologies=["Python", "Pandas", "SQLAlchemy", "Dataverse", "Faker"],
        repo_url=cast(HttpUrl,"https://github.com/Ajollyworld79/data-pipeline")
    ),

    Project(
        slug="the-cold-file",
        title="The Cold File — Autonomous AI True-Crime Podcast Channel",
        description=(
            "Production Python backend that fully operates a fictional dual-host true-crime podcast on YouTube — "
            "<a href='https://www.youtube.com/@The_Cold_File' target='_blank' rel='noopener noreferrer' style='color:#f2849e;'>@The_Cold_File</a> — "
            "with Claude wearing multiple intelligent hats across a single 30,000-line pipeline."
            "<!--more-->"
            "<strong>The show is a fictional dual-host podcast.</strong> Every case is AI-invented — no real names, locations, or events — which eliminates defamation, YouTube-strike, and family-complaint risk. Episodes run 9,000–11,000 words / 55–65 minutes of finished podcast audio rendered as YouTube video. The conversation is between two hosts: <em>Dr. Christy Hart</em> (criminal psychologist, always present) and a rotating male co-host — either <em>Jake Morgan</em> (investigative journalist, theory-heavy episodes) or <em>Marcus Reed</em> (retired homicide detective, investigation-heavy episodes). The male host is chosen deterministically via <code>hash(case_title) % 2</code> using the same formula in both the script-gen prompt and the TTS layer, so the persona named in the dialogue always matches the voice that gets played."
            "<br><br>"
            "<strong>Claude is not just the writer.</strong> Opus generates concepts and full dual-host scripts across 14 case types (<code>MURDER_MYSTERY</code>, <code>COLD_CASE</code>, <code>SERIAL_KILLER</code>, <code>KIDNAPPING</code>, <code>CULT</code>, <code>WRONGFUL_CONVICTION</code>, <code>FINANCIAL_CRIME</code>, <code>HEIST</code>, <code>STALKER_TO_MURDER</code>, <code>CORPORATE_CONSPIRACY</code>, <code>FAMILY_MURDER</code>, …) and 6 structural variants (linear chronology, case-file walkthrough, retrospective, whodunit, reverse-chronology, parallel investigations) — both rotated least-recently-used to keep the catalog fresh. "
            "A separate Sonnet pass is the <em>quality gate</em>: it scores N parallel candidate concepts against a weighted rubric (hook 35%, retention 30%, etc.) — only the winner enters production, losers are logged for prompt-tuning. "
            "Sonnet then plays <em>casting director</em>: it tunes Azure MultiTalker inference parameters (temperature/top_p/cfg_scale) per host to match the case's emotional register — measured clinical vs. urgent vs. retrospective. "
            "Claude also authors every per-scene image prompt, gated through case-file atmosphere maps and safety clauses (no recognizable faces, no celebrities, documentary framing only) — fictional cases must never produce imagery that resembles real victims or perpetrators."
            "<br><br>"
            "<strong>Image generation has a two-tier fallback.</strong> Primary path is Azure Flux 2 Pro; when Flux's content filter rejects a prompt (common on crime-scene imagery), the pipeline retries the original unmutated prompt via <em>Nano Banana</em> (Gemini 2.5 Flash Image through Fal.ai) which has a different filter profile — so a rejected scene still ships an image instead of falling back to a generic placeholder."
            "<br><br>"
            "<strong>Real-world signal in, abstracted prompt fuel out.</strong> A topical-signal miner pulls Google Trends + NewsAPI headlines from the true-crime space, then Claude distills them into structural <em>beat shapes</em> (e.g. \"DNA match decades later\", \"convicted-killer-dies cases reopen\") — never leaking real case names into the fictional show. Raw headlines stay in <code>raw_examples</code> for audit only. A title miner analyzes competitor channels for winning title structures, and a YouTube Analytics feedback loop produces weekly insights that feed back into concept generation."
            "<br><br>"
            "<strong>13+ Postgres tables</strong> track everything: <code>stories</code>, <code>concept_candidates</code>, <code>cold_open_attempts</code>, <code>video_performance</code>, <code>weekly_insights</code>, <code>title_patterns</code>, <code>topical_signals</code>, <code>comment_interactions</code>, <code>schedule</code>, plus dedup history that prevents repeating case concepts or titles. "
            "FFmpeg compiles 1080p video with <code>CASE FILE</code> / <code>COLD CASE</code> / <code>UNSOLVED</code> / <code>CASE CLOSED</code> thumbnail badges derived from the case's <code>resolution</code> field; YouTube Data API v3 handles uploads, Shorts trailers, and chapter markers. Runs hourly on Railway."
            "<br><br>"
            "<strong>Claude also runs the comment section.</strong> A Haiku-powered community engagement loop scans every uploaded video on two passes — a fast pass over the newest 15 videos every cycle to catch fresh comments, and a deep pass that rotates through the full back catalog so a comment on video #200 still gets answered within a day or two. Haiku writes the actual replies using a rotation of tone presets and pulls the original case context from Postgres so replies stay on-topic. Questions that need real case knowledge escalate to Sonnet. Daily YouTube API quota is tracked in DB and the loop self-throttles when it hits the limit."
            "<br><br>"
            "<em>Repository is private — contact guch79@gmail.com for access or commercial options.</em>"
        ),
        technologies=["Python", "Claude (Opus/Sonnet/Haiku)", "Anthropic SDK", "Azure Flux", "Nano Banana (Gemini Image)", "Azure MultiTalker TTS", "FFmpeg", "PostgreSQL", "YouTube API", "NewsAPI", "Railway"],
        live_url=cast(HttpUrl, "https://www.youtube.com/@The_Cold_File"),
    ),

]
