from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.snippet import Snippet
from backend.schemas.snippet import SnippetCreate

router = APIRouter()

# Existing route to save the code
@router.post("/save")
async def save_code(snippet_data: SnippetCreate, db: Session = Depends(get_db)):
    new_db_snippet = Snippet(
        title=snippet_data.title,
        code=snippet_data.code,
        language=snippet_data.language,
        user_email=snippet_data.user_email
    )
    db.add(new_db_snippet)
    db.commit()
    db.refresh(new_db_snippet)
    return {"message": "Code saved successfully!", "id": new_db_snippet.id}

# NEW route to fetch the saved code for the dashboard
@router.get("/list/{user_email}")
async def get_user_snippets(user_email: str, db: Session = Depends(get_db)):
    # Fetch all snippets for this user, ordering by newest first
    snippets = db.query(Snippet).filter(Snippet.user_email == user_email).order_by(Snippet.id.desc()).all()
    return snippets