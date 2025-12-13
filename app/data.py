from .models import Project

# Midlertidig in-memory data. Kan senere hentes fra database eller YAML/JSON fil.
PROJECTS = [
    Project(
        slug="llm-assistant",
        title="LLM Assistant & Retrieval System",
        description="Et produktionsklart LLM assistentprojekt med vektor-søgning, embeddings og prompt management.",
        technologies=["Python", "LangChain", "FAISS", "Docker", "LLM"],
        repo_url="https://github.com/Ajollyworld79/llm-assistant",
        live_url="https://example-llm-project.example.com"
    ),
    Project(
        slug="asynk-web-api",
        title="Asynkron Web API",
        description="Eksempel på en robust Quart service med caching og metrics.",
        technologies=["Quart", "Redis", "PostgreSQL"],
        repo_url="https://github.com/Ajollyworld79/asynk-web-api"
    ),
    Project(
        slug="data-pipeline",
        title="Data Pipeline",
        description="Automatiseret ETL pipeline til dataindsamling, transformation og modellering.",
        technologies=["Python", "Pandas", "Airflow"],
        repo_url="https://github.com/Ajollyworld79/data-pipeline"
    ),
]
