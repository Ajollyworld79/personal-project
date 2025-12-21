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
        title="Asynchronous Web API",
        description="Example of a robust Quart service with caching and metrics.",
        technologies=["Quart", "Async", "Qdrant"],
        repo_url=cast(HttpUrl,"https://github.com/Ajollyworld79/personal-project")
    ),
    Project(
        slug="data-pipeline",
        title="Dataverse to SQL Extract Pipeline",
        description="Production-ready script for extracting data from Microsoft Dataverse to SQL Server with parallel processing, connection pooling, and circuit breakers.",
        technologies=["Python", "Pandas", "SQLAlchemy", "Dataverse"],
        repo_url=cast(HttpUrl,"https://github.com/Ajollyworld79/data-pipeline")
    ),
]
