from .models import Project

# Temporary in-memory data. Can later be fetched from database or YAML/JSON file.
PROJECTS = [
    Project(
        slug="llm-assistant",
        title="LLM Assistant & Retrieval System",
        description="A production-ready LLM assistant project with vector search, embeddings, and prompt management.",
        technologies=["Python", "Qdrant", "Azure AI", "LLM"],
        repo_url="https://github.com/Ajollyworld79/llm-assistant",
        live_url="https://example-llm-project.example.com"
    ),
    Project(
        slug="asynk-web-api",
        title="Asynchronous Web API",
        description="Example of a robust Quart service with caching and metrics.",
        technologies=["Quart", "Azure AI", "PostgreSQL"],
        repo_url="https://github.com/Ajollyworld79/asynk-web-api"
    ),
    Project(
        slug="data-pipeline",
        title="Data Pipeline",
        description="Automated ETL pipeline for data collection, transformation, and modeling.",
        technologies=["Python", "Pandas", "Async", "Threading"],
        repo_url="https://github.com/Ajollyworld79/data-pipeline"
    ),
]
