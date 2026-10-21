import os
from fastapi import APIRouter
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv

# Load the secrets from the .env file
load_dotenv()

router = APIRouter()

# Securely fetch the API key from the environment
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

class AIRequest(BaseModel):
    code: str

@router.post("/analyze")
async def analyze_code(payload: AIRequest):
    code = payload.code.strip()
    
    if not code:
        return {"analysis": "It looks like your editor is empty. Write some code first!"}

    prompt = f"""
    You are an expert, encouraging AI coding tutor for a student. 
    The student has written the following Python code:
    
    ```python
    {code}
    ```
    
    Analyze this code. If there are syntax errors or logic bugs, gently point them out and provide helpful hints, but DO NOT give the exact final answer immediately. If the code is correct, briefly explain why it is good. Keep your response concise, using Markdown for bolding and bullet points. Do not exceed 150 words.
    """
    
    try:
        # THE FIX: We use the async client (client.aio) and 'await' it 
        # so it doesn't block the FastAPI server!
        response = await client.aio.models.generate_content(
            model='gemini-3.8-flash', # Note: Using standard model name for stability
            contents=prompt
        )
        return {"analysis": response.text}
    except Exception as e:
        return {"analysis": f"**Error connecting to AI:** {str(e)}"}