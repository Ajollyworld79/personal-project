from .models import Project

# Midlertidig in-memory data. Kan senere hentes fra database eller YAML/JSON fil.
PROJECTS = [
    Project(
        slug="asynk-web-api",
        title="Asynkron Web API",
        description="Eksempel på en robust FastAPI service med caching og metrics.",
        technologies=["FastAPI", "Redis", "PostgreSQL"],
        repo_url="https://github.com/Ajollyworld79/asynk-web-api"
    ),
    Project(
        slug="data-pipeline",
        title="Data Pipeline",
        description="Automatiseret ETL pipeline til datarens og berigelse.",
        technologies=["Python", "Pandas", "Airflow"],
        repo_url="https://github.com/Ajollyworld79/data-pipeline"
    ),
]
