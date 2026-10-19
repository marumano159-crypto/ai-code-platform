from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.snippet import Snippet # Adjust this import if your model file is named differently
from pydantic import BaseModel
from typing import List

router = APIRouter()

# Schema for incoming data
class SnippetCreate(BaseModel):
    title: str
    code: str
    language: str = "python"
    user_email: str

# 1. Existing Route: Saves the code to Supabase
@router.post("/save")
def save_snippet(snippet: SnippetCreate, db: Session = Depends(get_db)):
    new_snippet = Snippet(
        title=snippet.title,
        code=snippet.code,
        language=snippet.language,
        user_email=snippet.user_email
    )
    db.add(new_snippet)
    db.commit()
    db.refresh(new_snippet)
    return {"message": "Snippet saved successfully!", "id": new_snippet.id}

# 2. NEW Route: Fetches the code for the Student Dashboard
@router.get("/list/{user_email}")
def get_user_snippets(user_email: str, db: Session = Depends(get_db)):
    # Query Supabase for all snippets matching this email, ordered newest to oldest
    snippets = db.query(Snippet).filter(Snippet.user_email == user_email).order_by(Snippet.id.desc()).all()
    
    # Return an empty list if none exist, preventing frontend errors
    if not snippets:
        return []
        
    return snippets