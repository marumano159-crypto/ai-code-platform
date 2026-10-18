from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 1. Single, correct import with all 4 modules
from backend.api import auth, sockets, execute, ai, snippets
from backend.models import snippet
from backend.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Code Platform API")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Code Platform API", "status": "active"}

# 2. All 4 routers correctly registered
app.include_router(auth.router)
app.include_router(sockets.router)
app.include_router(execute.router, prefix="/api/execute", tags=["Execution"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI Tutor"])
app.include_router(snippets.router, prefix="/api/snippets", tags=["Snippets"])