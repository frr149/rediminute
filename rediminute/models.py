"""
Pydantic models for message validation
"""
from typing import Optional, Any
from pydantic import BaseModel


# Action constants
SET = "SET"
GET = "GET"
DEL = "DEL"
PING = "PING"


class Command(BaseModel):
    """
    Base command model for client requests
    """
    action: str
    key: Optional[str] = None
    value: Optional[str] = None
    namespace: Optional[str] = None


class Response(BaseModel):
    """
    Response model for server responses
    """
    status: str  # "ok" or "error"
    result: Optional[Any] = None
    error: Optional[str] = None
    code: Optional[int] = None 