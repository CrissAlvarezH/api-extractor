import json
from typing import Optional

from src.common.constants import API_KEYS_SECRET_NAME, CONFIG_HISTORY_TABLE_NAME, CONFIG_TABLE_NAME


class Response:
    status: int
    body: dict

    def __init__(self, body: Optional[dict] = None, status: int = 200):
        self.body = body
        self.status = status

    @property
    def json(self) -> dict:
        return {
            "statusCode": self.status,
            "body": json.dumps(self.body) if self.body else None,
            "headers": {
                "Content-Type": "application/json"
            }
        }

