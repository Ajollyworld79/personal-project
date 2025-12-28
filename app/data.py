from .models import Project
from typing import cast
from pydantic import HttpUrl

PROJECTS = [
    Project(
        slug="llm-assistant",
        title="AI-Powered Document Assistant with RAG",
        description="Production-ready Retrieval-Augmented Generation (RAG) system with multi-format document parsing (PDF, DOCX, CSV with link extraction), intelligent semantic chunking, and vector search using Qdrant. Features Azure OpenAI integration with conversation history, content filtering, adaptive garbage collection, API monitoring with performance alerts, and demo mode for offline testing. Built with async Quart backend, multiple embedding providers (SentenceTransformers, Azure, FastEmbed), and comprehensive lifecycle management.",
        technologies=["Python", "Quart", "Qdrant", "Azure OpenAI", "RAG", "Vector Search", "NLP"],
        repo_url=cast(HttpUrl,"https://github.com/Ajollyworld79/llm-assistant"),
        live_url=cast(HttpUrl,"https://llm-assistant-production.up.railway.app")
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
        description="A live Model Context Protocol (MCP) server that provides context-aware crisis communication for AI agents. Test it live right here with the 'Generate Live Apology' button, or connect your own agent via the GitHub instructions. Features multiple severity levels, styles (including Haiku), and SSE support.",
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
]
