from pydantic import BaseModel
from typing import Dict

class HealthStatus(BaseModel):
    postgresql: str
    redis: str
    elasticsearch: str
    details: Dict[str, str]

    class Config:
        json_schema_extra = {
            "example": {
                "postgresql": "connected",
                "redis": "connected",
                "elasticsearch": "connected",
                "details": {
                    "postgresql": "Successfully executed SELECT 1",
                    "redis": "PING returned PONG",
                    "elasticsearch": "Cluster health status: green"
                }
            }
        }
