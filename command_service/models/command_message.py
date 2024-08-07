from pydantic import BaseModel

class CommandMessage(BaseModel):
    command: str
    path: str = ""
