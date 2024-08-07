from fastapi import APIRouter
from models.command_message import CommandMessage
from services.command_service import run_command
from config.config import load_config
from services.logger import CustomLogger
from pydantic import BaseModel
import requests
import traceback
import os
import asyncio
import subprocess
router = APIRouter()

@router.post('/execute-bash')
async def command_service(message: CommandMessage):
    settings = load_config()
    logger = CustomLogger(settings)

    logger.error(f'Handling command: {message.command} in path: {message.path}')

    try:
        logger.info(f"Running command: {message.command} in path: {message.path}")

        # Determine the full path
        # Adjust the path relative to settings.bash_working_directory, unless it's a full path
        if message.path.startswith("/mnt"):
            full_path = message.path
        elif message.path == ".":
            full_path = settings.bash_working_directory
        else:
            full_path = os.path.join(settings.bash_working_directory, message.path.lstrip("./"))
        logger.error(f'full_path: {full_path}')

        process = await asyncio.create_subprocess_shell(
            message.command,
            cwd=full_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        logger.error(f'Command succeeded: stdout: {stdout.decode()}, stderr: {stderr.decode()}')
        return {'stdout': stdout.decode(), 'stderr': stderr.decode()}

    except Exception as e:
        logger.error(f'Failed to execute command: {str(e)}')
        return {'stdout': '', 'stderr': str(e)}


class ElasticQueryMessage(BaseModel):
    connection_string: str
    index: str
    query: dict

class ElasticLogMessage(BaseModel):
    connection_string: str
    index: str
    log: dict

@router.post('/elastic-query')
async def handle_elastic(message: ElasticQueryMessage):
    settings = load_config()
    logger = CustomLogger(settings)

    logger.info(f'Handling elastic: {message.connection_string}')

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

@router.post('/elastic-log')
async def handle_elastic_log(message: ElasticLogMessage):
    settings = load_config()
    logger = CustomLogger(settings)

    logger.info(f'Handling elastic log: {message.connection_string}')

    try:
        log_url = f"{message.connection_string}/{message.index}/_doc"
        logger.debug(f"Log URL: {log_url}")
        logger.debug(f"Log Body: {message.log}")

        response = requests.post(log_url, json=message.log)
        logger.debug(f"Response: {response.text}")
        response.raise_for_status()

        logger.info(f"Log succeeded: {response.json()}")
        return response.json()
    except requests.RequestException as e:
        error_message = f"Failed to send log to Elasticsearch: {str(e)}"
        logger.error(error_message)
        traceback_str = ''.join(traceback.format_tb(e.__traceback__))
        return {"error": error_message, "traceback": traceback_str}
