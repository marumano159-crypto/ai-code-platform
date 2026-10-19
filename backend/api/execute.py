from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import asyncio
import tempfile
import os

router = APIRouter()

# Keep the original HTTP route as a fallback
class CodePayload(BaseModel):
    code: str
    language: str = "python"
    user_input: str = ""

@router.post("/run")
async def run_code(payload: CodePayload):
    if payload.language != "python":
        raise HTTPException(status_code=400, detail="Only Python is supported currently.")

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_script:
        temp_script.write(payload.code)
        temp_filepath = temp_script.name

    try:
        result = await asyncio.create_subprocess_exec(
            "python", temp_filepath,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(result.communicate(input=payload.user_input.encode()), timeout=5)
        
        return {"output": stdout.decode(), "error": stderr.decode()}
    except asyncio.TimeoutError:
        return {"output": "", "error": "Error: Execution timed out (Possible infinite loop?)"}
    finally:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)

# NEW: Real-time WebSocket Execution Engine
@router.websocket("/ws/run")
async def interactive_run(websocket: WebSocket):
    await websocket.accept()
    process = None
    temp_filepath = None
    
    try:
        # 1. Wait for the frontend to send the code
        data = await websocket.receive_json()
        code = data.get("code", "")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_script:
            temp_script.write(code)
            temp_filepath = temp_script.name

        # 2. Start the process asynchronously
        process = await asyncio.create_subprocess_exec(
            "python", temp_filepath,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # 3. Define tasks to stream output line-by-line to the frontend
        async def stream_stdout():
            while line := await process.stdout.readline():
                await websocket.send_json({"type": "stdout", "data": line.decode()})

        async def stream_stderr():
            while line := await process.stderr.readline():
                await websocket.send_json({"type": "stderr", "data": line.decode()})

        # Run output streams in the background
        task_out = asyncio.create_task(stream_stdout())
        task_err = asyncio.create_task(stream_stderr())

        # 4. Continuously listen for user input from the frontend and pipe it to the process
        while True:
            user_input = await websocket.receive_text()
            if process.stdin:
                process.stdin.write((user_input + "\n").encode())
                await process.stdin.drain()

    except WebSocketDisconnect:
        pass # The user closed the browser or stopped the run
    finally:
        # 5. Clean up the process and temporary file
        if process:
            try:
                process.terminate()
            except ProcessLookupError:
                pass
        if temp_filepath and os.path.exists(temp_filepath):
            os.remove(temp_filepath)