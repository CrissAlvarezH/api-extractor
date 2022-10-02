from typing import Optional


class Response:
    status: int
    body: dict

    def __init__(self, body: Optional[dict] = None, status: int = 200):
        self.body = body
        self.status = status
