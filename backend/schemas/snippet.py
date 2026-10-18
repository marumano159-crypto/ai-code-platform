from pydantic import BaseModel
from datetime import datetime

# What the frontend sends to the backend
class SnippetCreate(BaseModel):
    title: str
    code: str
    language: str = "python"
    user_email: str

# What the backend sends back to the frontend
class SnippetResponse(SnippetCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True