from .models import Project
from typing import cast
from pydantic import HttpUrl

PROJECTS = [
    Project(
        slug="llm-assistant",
        title="AI-Powered IT Support Agent with RAG",
        description=(
            "Multilingual IT support agent that answers from customer-owned documentation. Runs in production with encrypted storage, hard cost controls, and an inspectable operations console."
            "<!--more-->"
            "<strong>Architecture.</strong> Async Quart app built by a <code>create_app()</code> factory with a Qdrant vector store on a persistent volume (chunk text AES-256-GCM encrypted at rest) and Gemini embeddings (<code>gemini-embedding-001</code>, 768-dim). Answers come from <code>gemini-3.5-flash-lite</code> at low reasoning effort, with <code>gemini-3.1-flash-lite</code> as a separate fallback; every model call is time-boxed, so a stuck call switches model instead of hanging. Questions can include images (multimodal), and documents are ingested from PDF, DOCX, TXT, Markdown and CSV — unsupported, empty or corrupt files are rejected rather than indexed."
            "<br><br>"
            "<strong>Structured, grounded answers.</strong> Every answer is structured output that states its source (documents, general knowledge or refusal), its language and any refusal reason. Prompt-injection attempts are refused, and truncated model output is recovered instead of failing the request."
            "<br><br>"
            "<strong>Cost guardrails for a public demo.</strong> Per-IP rate limits (per minute and per day), per-session message caps, and a persistent daily token budget written to disk so a restart loop cannot bypass it."
            "<br><br>"
            "<strong>Operations console at <code>/backend</code>.</strong> The public view shows model configuration sanitized through an allowlist so no key can leak, plus live usage metrics and rate-limit/budget status. Per-call token accounting (including cached tokens and fallback use) feeds a timeseries of requests, tokens, cache-hit ratio and fallback rate, and a searchable conversation log records embed/AI/total latency per exchange in Postgres, with PII redacted before storage. Operators sign in through an HttpOnly, SameSite=Strict session cookie with a CSRF header; documents, conversations, internals and every mutation fail closed without it."
            "<br><br>"
            "<strong>Security and quality.</strong> The chat page uses a signed session cookie, so no token ever reaches the browser; server-to-server callers, like the CV chat on this site, use a separate least-privilege token and are exempt from per-IP limits keyed on <code>X-Real-IP</code>. Strict same-origin CSP with no inline scripts or styles and all libraries vendored, input caps, and no query logging. 218 tests at 94% coverage, ruff and mypy clean, zero known dependency vulnerabilities, MIT licensed."
        ),
        technologies=["Python", "Quart", "Gemini 3.5 Flash-Lite", "google-genai", "Qdrant", "Gemini embeddings", "RAG", "PostgreSQL", "pytest", "Railway"],
        repo_url=cast(HttpUrl, "https://github.com/Ajollyworld79/llm-assistant"),
        live_url=cast(HttpUrl, "https://llm-assistant-production-aa36.up.railway.app/"),
        image="assets/images/projects/llm-assistant.webp",
    ),

    Project(
        slug="document-intelligence-pipeline",
        title="Document Intelligence Pipeline",
        description=(
            "Local-first pipeline that turns PDFs, DOCX files, and scans into structured JSON — including OCR, tables, key values, entities, layout, and summaries."
            "<!--more-->"
            "<strong>Pipeline.</strong> Each document is classified first, then OCR'd with Tesseract in the language you choose (for example <code>eng+dan</code>) or the one it detects; pages where OCR confidence is low fall back to handwriting recognition (Kraken/Calamari). Tables, key values, entities (spaCy), layout and a local TF-IDF summary are extracted, and progress streams live to the browser over Server-Sent Events. No external APIs — everything runs locally."
            "<br><br>"
            "<strong>Hardened for a public demo.</strong> Validated uploads with 10 MB / 30-page limits, at most two concurrent jobs, one document per hour per IP, hourly cleanup of uploads and results, a slim non-root Docker image and a CSP without inline JavaScript."
            "<br><br>"
            "Results are produced as structured JSON suitable for downstream ingestion (data lakes, BI, search indexes). "
            "Repository is private — contact guch79@gmail.com for access and commercial options."
        ),
        technologies=["Python", "Quart", "OCR", "Tesseract", "Kraken (HTR)", "spaCy", "PDF processing", "NLP", "SSE"],
        live_url=cast(HttpUrl,"https://document-intelligence-pipeline-production.up.railway.app"),
        image="assets/images/projects/document-intelligence-pipeline.webp",
    ),

    Project(
        slug="personal-project",
        title="Professional Portfolio & CV Generator",
        description=(
            "React and TypeScript 7 portfolio with a Python backend, where the website and downloadable PDF CV share one content source."
            "<!--more-->"
            "Prerendered React pages, a streaming CV assistant, live service checks, and an accessible video player. Vite builds the frontend; Quart serves it alongside the API and PDF generator."
        ),
        technologies=["React", "TypeScript 7", "Vite", "Quart", "FPDF2"],
        repo_url=cast(HttpUrl,"https://github.com/Ajollyworld79/personal-project"),
        image="assets/images/projects/personal-project.webp",
    ),
    Project(
        slug="apology-service",
        title="Apology-as-a-Service (MCP Server)",
        description=(
            "Public MCP server that gives AI agents context-aware crisis communication over Streamable HTTP (with SSE for older clients), plus an interactive demo and ready-to-use connection config."
            "<!--more-->"
            "Test it live right here with the 'Generate Live Apology' button, or "
            "<a href='/static/mcp-config.json' target='_blank' rel='noopener noreferrer' style='color:#f2849e;'>download the config</a> "
            "to connect your own agent to <code>/mcp</code>. Three tools: <code>generate_apology</code> (5 severity levels × 15 styles, from Haiku and Shakespearean to Gen Z, Viking and Soap Opera), "
            "<code>escalation_ladder</code> (the same apology at every severity level) and <code>rate_my_apology</code> (scores sincerity, cringe and hedging 0–10 with a one-line verdict), plus a <code>save_my_ass</code> crisis prompt."
        ),
        technologies=["Python", "MCP Protocol", "Streamable HTTP", "SSE", "FastMCP", "Docker"],
        repo_url=cast(HttpUrl, "https://github.com/Ajollyworld79/Apology-as-a-Service"),
        live_url=cast(HttpUrl, "https://apology-as-a-service-production.up.railway.app/"),
        image="assets/images/projects/apology-service.svg",
    ),
    Project(
        slug="data-pipeline",
        title="ETL Data Pipeline - Dataverse to SQL Server",
        description=(
            "Production-style ETL from Microsoft Dataverse to SQL Server with parallel extraction, business-rule transforms, connection pooling, and circuit breakers."
            "<!--more-->"
            "Includes fake data generation with Faker for testing before production deployment. Features parallel processing, connection pooling, and circuit breakers."
        ),
        technologies=["Python", "Pandas", "SQLAlchemy", "Dataverse", "Faker"],
        repo_url=cast(HttpUrl,"https://github.com/Ajollyworld79/data-pipeline"),
        image="assets/images/projects/data-pipeline.svg",
    ),

    Project(
        slug="the-cold-file",
        title="The Cold File — Autonomous AI True-Crime Podcast Channel",
        description=(
            "Autonomous Python pipeline that turns a concept into a full-length YouTube episode — script, quality gate, voices, images, render, upload, and comment replies — with zero human edits. Watch it live at "
            "<a href='https://www.youtube.com/@The_Cold_File' target='_blank' rel='noopener noreferrer' style='color:#f2849e;'>@The_Cold_File</a> — "
            "running hourly on Railway."
            "<!--more-->"
            "<strong>The show is a fictional dual- or triple-host podcast.</strong> Every case is AI-invented — no real names, locations, or events — which eliminates defamation, YouTube-strike, and family-complaint risk. Two length profiles keep episodes tight: compact (6,500–7,500 words, about 40–47 minutes) and standard (8,000–9,500 words, about 50–60 minutes) of finished podcast audio rendered as YouTube video; listener calls and guest turns count against the same word budget. Earlier episodes ran longer, up to 75 minutes. <em>Dr. Christy Hart</em> (criminal psychologist) hosts every episode with a male co-host who strictly alternates from one episode to the next — <em>Jake Morgan</em> (investigative journalist) or <em>Marcus Reed</em> (retired LAPD homicide detective). The pick is pinned on the concept, so the persona named in the dialogue always matches the voice the TTS layer plays. "
            "On guest episodes a recurring specialist joins as a third host for the whole episode — a forensic pathologist, a private investigator, a retired crime reporter, a digital-forensics analyst, or a defense attorney — matched to the case type, with memory of their earlier cases so the hosts can refer back to them. Listener call-ins add new ground mid-episode."
            "<br><br>"
            "<strong>GPT-6 writes, judges and casts.</strong> Azure OpenAI <em>GPT-6 Sol</em> (public OpenAI as fallback) generates concepts and full multi-voice scripts — act by act, at high reasoning effort — across 14 case types (<code>MURDER_MYSTERY</code>, <code>COLD_CASE</code>, <code>SERIAL_KILLER</code>, <code>KIDNAPPING</code>, <code>CULT</code>, <code>WRONGFUL_CONVICTION</code>, <code>FINANCIAL_CRIME</code>, <code>HEIST</code>, <code>STALKER_TO_MURDER</code>, <code>CORPORATE_CONSPIRACY</code>, <code>FAMILY_MURDER</code>, …) and 6 structural variants (linear chronology, case-file walkthrough, retrospective, whodunit, reverse-chronology, parallel investigations) — both rotated least-recently-used to keep the catalog fresh. "
            "A separate Sol pass is the <em>quality gate</em> (LLM-as-judge): it scores three candidate concepts against a weighted rubric (hook 35%, retention 30%, twist 20%, visual 15%) — only the winner enters production, losers are logged for prompt-tuning. "
            "Sol also plays <em>casting director</em> for everyone outside the studio — listener callers, 911 operators, news reporters, recordings — choosing from tiered Azure Dragon HD Omni and HD voices, while hosts and guests speak through Azure's multi-speaker Dragon HD MultiTalker model. "
            "GPT-6 also authors every per-scene image prompt, gated through case-file atmosphere maps and safety clauses (no recognizable faces, no celebrities, documentary framing only) — fictional cases must never produce imagery that resembles real victims or perpetrators."
            "<br><br>"
            "<strong>Image generation has a fallback.</strong> Primary path is Azure OpenAI <em>GPT Image 2.5</em>. When Azure rejects a single prompt (common on crime-scene imagery), that one image is retried on the same model through fal.ai and the next image goes back to Azure; other Azure failures trigger a cooldown — so a rejected scene still ships an image instead of a generic placeholder."
            "<br><br>"
            "<strong>Real-world signal in, abstracted prompt fuel out.</strong> A topical-signal miner pulls Google Trends + NewsAPI headlines from the true-crime space, then GPT-6 distills them into structural <em>beat shapes</em> (e.g. \"DNA match decades later\", \"convicted-killer-dies cases reopen\") — never leaking real case names into the fictional show. Raw headlines stay in <code>raw_examples</code> for audit only. A title miner analyzes competitor channels for winning title structures, and a YouTube Analytics feedback loop produces weekly insights that feed back into concept generation."
            "<br><br>"
            "<strong>13 Postgres tables</strong> track everything: <code>stories</code>, <code>concept_candidates</code>, <code>cold_open_attempts</code>, <code>video_performance</code>, <code>weekly_insights</code>, <code>title_patterns</code>, <code>topical_signals</code>, <code>comment_interactions</code>, <code>schedule</code>, plus dedup history that prevents repeating case concepts or titles. "
            "FFmpeg renders 1440p video (2560×1440) with <code>CASE FILE</code> / <code>COLD CASE</code> / <code>UNSOLVED</code> / <code>CASE CLOSED</code> thumbnail badges derived from the case's <code>resolution</code> field; YouTube Data API v3 handles uploads, Shorts trailers, and chapter markers. The scheduler wakes up hourly on Railway; episodes release on a persisted, randomized 5–8 day schedule."
            "<br><br>"
            "<strong>GPT-6 also runs the comment section.</strong> A community engagement loop scans every uploaded video on two passes — a fast pass over the newest 15 videos every cycle to catch fresh comments, and a deep pass that rotates through the full back catalog so a comment on video #200 still gets answered within a day or two. Sol writes the replies with a rotation of tone presets and pulls the original case context from Postgres so replies stay on-topic. Daily YouTube API quota is tracked in DB and the loop self-throttles when it hits the limit."
            "<br><br>"
            "<em>Repository is private — contact guch79@gmail.com for access or commercial options.</em>"
        ),
        technologies=["Python", "Azure OpenAI (GPT-6 Sol/Luna)", "OpenAI API", "LLM-as-judge", "GPT Image 2.5", "fal.ai", "Azure Speech (Dragon HD)", "FFmpeg", "PostgreSQL", "YouTube API", "NewsAPI", "Railway"],
        live_url=cast(HttpUrl, "https://www.youtube.com/@The_Cold_File"),
        image="assets/images/projects/the-cold-file.jpg",
    ),

    Project(
        slug="ai-trader",
        title="AI-Trader — Security-First Trading Platform for Saxo",
        description=(
            "Trading platform in Python where deterministic market analysis and risk management decide everything that touches money — AI may only classify. <strong>Not tested yet:</strong> it runs in paper/Saxo SIM mode by default and has not traded real money."
            "<!--more-->"
            "<strong>AI can never size a trade.</strong> Position size, stop loss, take profit, exposure and order approval are computed in Python. AI (GPT-5.4 Mini on Azure OpenAI with OpenAI as fallback, escalating to GPT-5.4 only when uncertain and for at most 5% of calls) only classifies, and a missing provider fails closed to <code>hold</code>. Every provider attempt is logged with model, tokens, latency and price."
            "<br><br>"
            "<strong>Risk engine.</strong> 0.5% risk per trade, at most 10 positions, 20% sector exposure, 2% daily loss and 10% drawdown limits; long-only, no leverage, with spread, earnings and data-quality checks. A deterministic market-regime classifier on Saxo benchmark data rejects new longs in bearish or extremely volatile markets before AI is consulted."
            "<br><br>"
            "<strong>Safe order flow.</strong> An order accepts only a fresh, stored buy signal that can be used once; prices, account value, exposure, stop, target and quantity are fetched or computed server-side, and Saxo's pre-check runs before an entry with broker-native related stop/take-profit orders. Order POSTs are never retried automatically, positions are reconciled with a high-watermark trailing stop, and Saxo OAuth tokens are stored encrypted and rotated behind a database lease."
            "<br><br>"
            "<strong>Research and operations.</strong> Deterministic indicators (EMA, SMA, RSI, ATR, MACD, ADX, Bollinger Bands, volume profile, …), an event-driven backtester with commission, spread, slippage, dividends, splits and walk-forward windows, Alpha Vantage news sentiment and earnings calendar treated as untrusted input, and separate worker roles on Railway. Quality gates: pytest with at least 80% coverage, ruff, black, mypy, bandit and pip-audit. LIVE trading is off by default and needs the kill switch released plus a separate confirmation token."
            "<br><br>"
            "<em>Work in progress and not financial advice — not yet tested against a live account.</em>"
        ),
        technologies=["Python", "FastAPI", "PostgreSQL", "SQLAlchemy", "Alembic", "Saxo OpenAPI", "Azure OpenAI", "Alpha Vantage", "Railway"],
        repo_url=cast(HttpUrl, "https://github.com/Ajollyworld79/AI-Trader"),
    ),

]

# Display order — strongest projects first on /projects.
_ORDER = [
    "the-cold-file",
    "llm-assistant",
    "document-intelligence-pipeline",
    "apology-service",
    "ai-trader",
    "data-pipeline",
    "personal-project",
]
PROJECTS.sort(key=lambda p: _ORDER.index(p.slug) if p.slug in _ORDER else len(_ORDER))
