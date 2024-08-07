import asyncio
import logging
import os
from config.config import Settings

async def run_command(command: str, path: str, settings: Settings, logger: logging.Logger):
    logger.info(f"Running command: {command} in path: {path}")

    logger.error(f"Running command: {command} in path: {path}")

    # Determine the full path
    # Adjust the path relative to settings.bash_working_directory, unless it's a full path
    if path.startswith("/mnt"):
        full_path = path
    elif path == ".":
        full_path = settings.bash_working_directory
    else:
        full_path = os.path.join(settings.bash_working_directory, path.lstrip("./"))
    logger.error(f'full_path: {full_path}')


    process = await asyncio.create_subprocess_shell(
        command,
        cwd=full_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    return stdout.decode(), stderr.decode()
