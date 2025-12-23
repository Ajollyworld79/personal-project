from .models import Project
from typing import cast
from pydantic import HttpUrl

PROJECTS = [
    Project(
        slug="llm-assistant",
        title="LLM Assistant & Retrieval System",
        description="A production-ready LLM assistant project with vector search, embeddings, and prompt management.",
        technologies=["Python", "Qdrant", "Azure AI", "LLM"],
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
        slug="data-pipeline",
        title="ETL Data Pipeline - Dataverse to SQL Server",
        description="Complete ETL pipeline for extracting data from Microsoft Dataverse, transforming with business logic, and loading to SQL Server. Includes fake data generation with Faker for testing before production deployment. Features parallel processing, connection pooling, and circuit breakers.",
        technologies=["Python", "Pandas", "SQLAlchemy", "Dataverse", "Faker"],
        repo_url=cast(HttpUrl,"https://github.com/Ajollyworld79/data-pipeline")
    ),
]
