from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
import logging
import requests
import traceback

app = FastAPI()
logging.basicConfig(level=logging.DEBUG)


class ElasticQueryMessage(BaseModel):
    connection_string: str
    index: str
    query: dict


class RegisterRequest(BaseModel):
    service_name: str
    url: str


PROXY_URL = "http://localhost:8080/register"


@app.on_event("startup")
async def startup_event():
    registration_data = {
        "service_name": "handle-elastic",
        "url": "http://localhost:8007"
    }
    try:
        logging.info("Registering service with the proxy...")
        response = requests.post(PROXY_URL, json=registration_data)
        response.raise_for_status()
        logging.info("Service registered successfully with the proxy.")
    except requests.RequestException as e:
        logging.error(f"Failed to register service with proxy: {e}")
        raise HTTPException(status_code=500, detail="Failed to register service with proxy")


@app.post("/handle-elastic")
async def handle_elastic(message: ElasticQueryMessage):
    logger = logging.getLogger(__name__)
    logger.info(f"Handling ElasticSearch query: {message}")

    try:
        query_url = f"{message.connection_string}/{message.index}/_search"
        logger.debug(f"Query URL: {query_url}")
        logger.debug(f"Query Body: {message.query}")

        response = requests.post(query_url, json={"query": message.query})
        logger.debug(f"Response: {response.text}")
        response.raise_for_status()

        logger.info(f"Query succeeded: {response.json()}")
        return response.json()
    except requests.RequestException as e:
        error_message = f"Failed to execute ElasticSearch query: {str(e)}"
        logger.error(error_message)
        traceback_str = ''.join(traceback.format_tb(e.__traceback__))
        return {"error": error_message, "traceback": traceback_str}

class ElasticQueryMessage(BaseModel):
    connection_string: str
    index: str
    query: dict


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8007)
