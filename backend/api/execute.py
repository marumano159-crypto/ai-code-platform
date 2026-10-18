from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import subprocess
import tempfile
import os

router = APIRouter()

# Define the structure of the incoming request
class CodePayload(BaseModel):
    code: str
    language: str = "python"

@router.post("/run")
async def run_code(payload: CodePayload):
    if payload.language != "python":
        raise HTTPException(status_code=400, detail="Only Python is supported currently.")

    # 1. Create a temporary file to safely store the user's code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_script:
        temp_script.write(payload.code)
        temp_filepath = temp_script.name

    try:
        # 2. Execute the file using Python and capture the terminal output
        # We use a 5-second timeout to prevent infinite loops from crashing the server
        result = subprocess.run(
            ["python", temp_filepath],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # 3. Return the standard output and any errors
        return {
            "output": result.stdout,
            "error": result.stderr
        }
        
    except subprocess.TimeoutExpired:
        return {"output": "", "error": "Error: Execution timed out (Possible infinite loop?)"}
    finally:
        # 4. ALWAYS clean up and delete the temporary file after running
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)