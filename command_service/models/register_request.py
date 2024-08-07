from typing import Optional, Dict, Any
from pydantic import BaseModel

class RegisterRequest(BaseModel):
    service_name: str
    openapi_url: Optional[str] = None  # Make this field optional
    openapi_json: Optional[Dict[str, Any]] = None  # Make this field optional and ensure it's a dictionary
