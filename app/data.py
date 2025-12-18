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
        live_url=cast(HttpUrl,"https://example-llm-project.example.com")
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
        title="Data Pipeline",
        description="Automated ETL pipeline for data collection, transformation, and modeling.",
        technologies=["Python", "Pandas", "Async", "Threading"],
        repo_url=cast(HttpUrl,"https://github.com/Ajollyworld79/data-pipeline")
    ),
]
