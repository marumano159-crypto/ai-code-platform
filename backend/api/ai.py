from fastapi import APIRouter
from pydantic import BaseModel
from google import genai

router = APIRouter()

# Initialize the new Gemini Client
api_key="YOUR_API_KEY_HERE"

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
        # The new syntax for generating content
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt
        )
        return {"analysis": response.text}
    except Exception as e:
        return {"analysis": f"**Error connecting to AI:** {str(e)}"}