import json

import boto3

from .constants import (
    CONFIG_HISTORY_TABLE_NAME, CONFIG_TABLE_NAME, API_KEYS_SECRET_NAME,
    EXTRACTOR_SECRETS_SECRET_NAME
)


def config_db_table():
    db = boto3.resource("dynamodb")
    table = db.Table(CONFIG_TABLE_NAME)
    history_table = db.Table(CONFIG_HISTORY_TABLE_NAME)
    return table, history_table


def get_secret_value(secret_id: str):
    client = boto3.client("secretsmanager")
    secret = client.get_secret_value(SecretId=API_KEYS_SECRET_NAME)
    value = json.loads(secret.get("SecretString"))
    return client, value


def api_keys_secrets():
    return get_secret_value(API_KEYS_SECRET_NAME)


def extractor_secrets():
    return get_secret_value(EXTRACTOR_SECRETS_SECRET_NAME)
