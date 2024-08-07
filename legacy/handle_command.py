from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
import asyncio
import logging
import os
import requests
from contextlib import asynccontextmanager
from handle_base import HandleBase

app = FastAPI()
logging.basicConfig(level=logging.INFO)

class CommandMessage(BaseModel):
    command: str
    path: str = ""

class RegisterRequest(BaseModel):
    service_name: str
    url: str

PROXY_URL = "http://localhost:8010/register"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Registration logic
    registration_data = {
        "service_name": "handle-command",
        "url": "http://localhost:8003"
    }
    try:
        logging.info(f"Registering service with the websocket listener at {PROXY_URL}...{registration_data}")
        response = requests.post(PROXY_URL, json=registration_data)
        response.raise_for_status()
        logging.info("Service registered successfully with the proxy.")
    except requests.RequestException as e:
        logging.error(f"Failed to register service with proxy: {e}")
        raise HTTPException(status_code=500, detail="Failed to register service with proxy")
    yield
    # Any cleanup logic here if needed

app = FastAPI(lifespan=lifespan)

async def run_command(command: str, path: str):
    logger = logging.getLogger(__name__)
    logger.info(f"Running command: {command} in path: {path}")

    full_path = os.path.abspath(path) if path else os.getcwd()

    process = await asyncio.create_subprocess_shell(
        command,
        cwd=full_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    return stdout.decode(), stderr.decode()

@app.post("/handle-command")
async def handle_command(message: CommandMessage):
    logger = logging.getLogger(__name__)
    logger.info(f"Handling command: {message.command} in path: {message.path}")

    try:
        stdout, stderr = await run_command(message.command, message.path)

        if stderr:
            logger.error(f"Command execution failed: {stderr}")
            return {"stdout": stdout, "stderr": stderr}

        logger.info(f"Command succeeded: stdout: {stdout}, stderr: {stderr}")
        return {"stdout": stdout, "stderr": stderr}

    except Exception as e:
        logger.error(f"Failed to execute command: {str(e)}")
        return {"stdout": "", "stderr": str(e)}

# Include the router from HandleBase
handle_base = HandleBase()
app.include_router(handle_base.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
