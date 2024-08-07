import requests
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
import json

app = FastAPI()

class CodeExecutionRequest(BaseModel):
    language: str
    version: str
    code: str

@app.post("/execute")
def execute_code(request: CodeExecutionRequest):
    url = "https://emkc.org/api/v2/piston/execute"
    payload = {
        "language": request.language,
        "version": request.version,
        "files": [{"name": "main", "content": request.code}]
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail="Error executing code")


def register_service():
    service_name = "handle_piston"
    service_url = "http://localhost:8002"
    proxy_url = "http://localhost:8080/register_service"
    payload = {
        "service_name": service_name,
        "url": service_url
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(proxy_url, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"Service {service_name} registered successfully.")
    else:
        print(f"Failed to register service {service_name}: {response.status_code}")

if __name__ == "__main__":
    register_service()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
