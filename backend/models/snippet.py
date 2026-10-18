from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from backend.database import Base

class Snippet(Base):
    __tablename__ = "snippets"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, index=True)  # Links the code to the logged-in user
    title = Column(String)                   # e.g., "My First Calculator"
    code = Column(Text)                      # The actual Python code
    language = Column(String, default="python")
    created_at = Column(DateTime(timezone=True), server_default=func.now())