from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
import logging
import os
import traceback
import requests
from contextlib import asynccontextmanager

app = FastAPI()
logging.basicConfig(level=logging.INFO)

class RegisterRequest(BaseModel):
    service_name: str
    url: str

PROXY_URL = "http://localhost:8001/register"

@asynccontextmanager
async def lifespan(app: FastAPI):
    registration_data = {
        "service_name": "handle-replit",
        "url": "http://localhost:8007/handle-replit"
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
    logging.info("Shutting down...")

app = FastAPI(lifespan=lifespan)

@app.post("/handle-replit")
async def handle_replit(file: UploadFile = File(...), repl_name: str = Form(...), repl_url: str = Form(...)):
    logger = logging.getLogger(__name__)
    logger.info(f"Handling file upload: {file.filename}")
    logger.info(f"Received repl_name: {repl_name}")
    logger.info(f"Received repl_url: {repl_url}")

    try:
        file_path = os.path.join(f"/home/runner/{repl_name}/", file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())

        file_url = f"https://{repl_url}/{file.filename}"
        logger.info(f"File uploaded successfully: {file_url}")
        return {"message": "File successfully uploaded", "url": file_url}
    except Exception as e:
        error_message = f"Failed to upload file: {str(e)}"
        logger.error(error_message)
        traceback_str = ''.join(traceback.format_tb(e.__traceback__))
        return {"error": error_message, "traceback": traceback_str}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
