from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class Project(BaseModel):
    slug: str
    title: str
    description: str
    technologies: List[str]
    repo_url: Optional[HttpUrl] = None
    live_url: Optional[HttpUrl] = None

class ProjectsResponse(BaseModel):
    projects: List[Project]
