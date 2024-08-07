from pydantic import BaseModel, Field
from typing import Any, Optional


class Envelope(BaseModel):
    endpoint_service_name: str = Field(..., description="Name of the service to forward the request to")
    endpoint_path: str = Field(..., description="Path of the service endpoint")
    endpoint_request_type: str = Field(..., description="HTTP method of the request (GET, POST, etc.)")
    endpoint_headers: Any = Field(default={}, description="Headers to include in the forwarded request")
    endpoint_params: Any = Field(default={}, description="Query parameters to include in the forwarded request")
    endpoint_body: Any = Field(default={}, description="Body of the forwarded request")
    connection_id: Optional[str] = Field(None, description="Connection ID for WebSocket listener")
   # endpoint_url: str = Field(..., description="URL of the service to register")