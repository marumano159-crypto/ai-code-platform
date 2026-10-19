from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import asyncio
import tempfile
import os

router = APIRouter()

class CodePayload(BaseModel):
    code: str
    language: str = "python"
    user_input: str = ""

# NEW: The router map that tells the backend which engine to use
EXECUTION_MAP = {
    "python": {"cmd": "python", "ext": ".py"},
    "javascript": {"cmd": "node", "ext": ".js"}
}

@router.post("/run")
async def run_code(payload: CodePayload):
    if payload.language not in EXECUTION_MAP:
        raise HTTPException(status_code=400, detail=f"Language {payload.language} is not supported.")

    config = EXECUTION_MAP[payload.language]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix=config["ext"], delete=False) as temp_script:
        temp_script.write(payload.code)
        temp_filepath = temp_script.name

    try:
        result = await asyncio.create_subprocess_exec(
            config["cmd"], temp_filepath,
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

@router.websocket("/ws/run")
async def interactive_run(websocket: WebSocket):
    await websocket.accept()
    process = None
    temp_filepath = None
    
    try:
        data = await websocket.receive_json()
        code = data.get("code", "")
        # NEW: Securely extracts the language selected in your frontend dropdown
        language = data.get("language", "python")

        if language not in EXECUTION_MAP:
            await websocket.send_json({"type": "stderr", "data": f"Unsupported language: {language}\n"})
            return

        config = EXECUTION_MAP[language]

        # NEW: Uses the correct file extension (.js or .py)
        with tempfile.NamedTemporaryFile(mode='w', suffix=config["ext"], delete=False) as temp_script:
            temp_script.write(code)
            temp_filepath = temp_script.name

        # NEW: Uses the correct terminal command (node or python)
        process = await asyncio.create_subprocess_exec(
            config["cmd"], temp_filepath,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        async def stream_stdout():
            while line := await process.stdout.readline():
                await websocket.send_json({"type": "stdout", "data": line.decode()})

        async def stream_stderr():
            while line := await process.stderr.readline():
                await websocket.send_json({"type": "stderr", "data": line.decode()})

        task_out = asyncio.create_task(stream_stdout())
        task_err = asyncio.create_task(stream_stderr())

        while True:
            user_input = await websocket.receive_text()
            if process.stdin:
                process.stdin.write((user_input + "\n").encode())
                await process.stdin.drain()

    except WebSocketDisconnect:
        pass 
    finally:
        if process:
            try:
                process.terminate()
            except ProcessLookupError:
                pass
        if temp_filepath and os.path.exists(temp_filepath):
            os.remove(temp_filepath)