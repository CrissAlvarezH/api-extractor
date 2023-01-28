import json
from typing import Optional
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


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
            "body": json.dumps(self.body, cls=DecimalEncoder) if self.body else None,
            "headers": {
                "Content-Type": "application/json"
            }
        }

