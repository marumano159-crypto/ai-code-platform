from sqlalchemy import Column, Integer, String, Text
from backend.database import Base

class Snippet(Base):
    __tablename__ = "snippets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    code = Column(Text)
    language = Column(String, default="python")
    user_email = Column(String, index=True)