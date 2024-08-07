from pydantic import BaseModel

class DeregisterRequest(BaseModel):
    service_name: str
