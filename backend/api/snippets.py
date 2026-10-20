from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.snippet import Snippet 
from pydantic import BaseModel
from typing import List

router = APIRouter()

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

# 2. Existing Route: Fetches code for a specific student
@router.get("/list/{user_email}")
def get_user_snippets(user_email: str, db: Session = Depends(get_db)):
    snippets = db.query(Snippet).filter(Snippet.user_email == user_email).order_by(Snippet.id.desc()).all()
    if not snippets:
        return []
    return snippets

# 3. NEW Route: Admin/Teacher access to fetch ALL platform snippets
@router.get("/all")
def get_all_snippets(db: Session = Depends(get_db)):
    # Pulls every saved project, ordered newest to oldest
    snippets = db.query(Snippet).order_by(Snippet.id.desc()).all()
    if not snippets:
        return []
    return snippets