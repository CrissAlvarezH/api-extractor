import json
from typing import Optional

import boto3

from src.api.constants import API_KEYS_SECRET_NAME, CONFIG_HISTORY_TABLE_NAME, CONFIG_TABLE_NAME


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


def config_db_table():
    db = boto3.resource("dynamodb")
    table = db.Table(CONFIG_TABLE_NAME)
    history_table = db.Table(CONFIG_HISTORY_TABLE_NAME)

    return table, history_table


def api_keys_secrets():
    client = boto3.client("secretsmanager")
    secret = client.get_secret_value(SecretId=API_KEYS_SECRET_NAME)
    api_keys = json.loads(secret.get("SecretString"))
    return client, api_keys
