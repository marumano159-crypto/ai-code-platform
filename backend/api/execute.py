from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import asyncio
import tempfile
import os
import re

router = APIRouter()

class CodePayload(BaseModel):
    code: str
    language: str = "python"
    user_input: str = ""

EXECUTION_MAP = {
    "python": {"cmd": "python", "ext": ".py"},
    "javascript": {"cmd": "node", "ext": ".js"}
}

# --- NEW: Enterprise Security Firewall ---
DANGEROUS_PATTERNS = {
    "python": [
        r"import\s+(os|subprocess|sys|shutil|pty|socket)",
        r"from\s+(os|subprocess|sys|shutil|pty|socket)\s+import",
        r"__import__", r"eval\(", r"exec\(", r"open\("
    ],
    "javascript": [
        r"require\(['\"](fs|child_process|os|net|http)['\"]\)",
        r"import\s+.*\s+from\s+['\"](fs|child_process|os|net|http)['\"]",
        r"eval\(", r"process\.exit"
    ]
}

def security_scan(code: str, language: str) -> str | None:
    """Scans code for dangerous patterns and returns an error message if found."""
    if language in DANGEROUS_PATTERNS:
        for pattern in DANGEROUS_PATTERNS[language]:
            if re.search(pattern, code):
                return f"🔒 Security Exception: Dangerous operation detected and blocked by platform firewall. Pattern matched: {pattern}"
    return None
# ----------------------------------------

@router.post("/run")
async def run_code(payload: CodePayload):
    if payload.language not in EXECUTION_MAP:
        raise HTTPException(status_code=400, detail=f"Language {payload.language} is not supported.")

    # Run security scan before anything else
    security_error = security_scan(payload.code, payload.language)
    if security_error:
        return {"output": "", "error": security_error}

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
        # Added stricter timeout for infinite loop protection
        stdout, stderr = await asyncio.wait_for(result.communicate(input=payload.user_input.encode()), timeout=5)
        return {"output": stdout.decode(), "error": stderr.decode()}
    except asyncio.TimeoutError:
        return {"output": "", "error": "⏳ Timeout Error: Execution exceeded 5 seconds (Possible infinite loop blocked)."}
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
        language = data.get("language", "python")

        if language not in EXECUTION_MAP:
            await websocket.send_json({"type": "stderr", "data": f"Unsupported language: {language}\n"})
            return

        # Run security scan on live WebSocket execution
        security_error = security_scan(code, language)
        if security_error:
            await websocket.send_json({"type": "stderr", "data": f"{security_error}\n"})
            return

        config = EXECUTION_MAP[language]

        with tempfile.NamedTemporaryFile(mode='w', suffix=config["ext"], delete=False) as temp_script:
            temp_script.write(code)
            temp_filepath = temp_script.name

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
            try:
                # Add timeout to waiting for user input to prevent stale socket connections hanging the server
                user_input = await asyncio.wait_for(websocket.receive_text(), timeout=300)
                if process.stdin:
                    process.stdin.write((user_input + "\n").encode())
                    await process.stdin.drain()
            except asyncio.TimeoutError:
                break

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