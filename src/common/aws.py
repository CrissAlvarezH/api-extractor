import json

import boto3

from .constants import CONFIG_HISTORY_TABLE_NAME, CONFIG_TABLE_NAME, API_KEYS_SECRET_NAME


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
