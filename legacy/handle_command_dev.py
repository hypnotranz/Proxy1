from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
import subprocess
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

PROXY_URL = "http://localhost:8005/register"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Registration logic
    registration_data = {
        "service_name": "handle-command-dev",
        "url": "http://localhost:8004"
    }
    try:
        logging.info("Registering service with the proxy...")
        response = requests.post(PROXY_URL, json=registration_data)
        response.raise_for_status()
        logging.info("Service registered successfully with the proxy.")
    except requests.RequestException as e:
        logging.error(f"Failed to register service with proxy: {e}")
        raise HTTPException(status_code=500, detail="Failed to register service with proxy")
    yield
    # Any cleanup logic here if needed

app = FastAPI(lifespan=lifespan)

@app.post("/handle-command-dev")
async def handle_command(message: CommandMessage):
    logger = logging.getLogger(__name__)
    logger.info(f"Handling command: {message} ")


    logger.info(f"Handling command: {message.command} in path: {message.path}")

    # Use the current working directory if path is not specified
    full_path = os.path.abspath(message.path) if message.path else os.getcwd()

    try:
        process = subprocess.Popen(
            message.command,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=full_path
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            error_message = stderr if stderr else f"Command failed with exit status {process.returncode}"
            logger.error(f"Command execution failed: {error_message}")
            return {"stdout": stdout, "stderr": stderr}

        logger.info(f"Command succeeded: stdout: {stdout}, stderr: {stderr}")
        return {"stdout": stdout, "stderr": stderr}

    except Exception as e:
        logger.error(f"Failed to execute command: {str(e)}")
        return {"stdout": stdout, "stderr": stderr}


# Include the router from HandleBase
handle_base = HandleBase()
app.include_router(handle_base.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
