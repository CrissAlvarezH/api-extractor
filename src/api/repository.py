import json
from typing import Optional, Union
from datetime import datetime
from uuid import uuid4

import boto3
from boto3.dynamodb.conditions import Key

from src.api.schemas import ApiConfig

# API CONFIG 

def list_api_configs() -> dict:
    db = boto3.resource("dynamodb")
    table = db.Table("ApiExtractorConfig")
    resp = table.scan()
    return resp


def list_api_config_history(id: str, updated_after_that: str) -> dict:
    db = boto3.resource("dynamodb")
    table = db.Table("ApiExtractorConfigHistory")

    params = {
        "KeyConditionExpression": Key("id").eq(id),
        "Limit": 50,
    }

    if updated_after_that:
        params["ExclusiveStartKey"] = {"id": id, "updated_at": updated_after_that}

    return table.query(**params)


def get_api_config(id: str) -> dict:
    db = boto3.resource("dynamodb")
    table = db.Table("ApiExtractorConfig")
    return table.get_item(Key={"id": id})


def insert_config(api_key: str, body: dict, id: Optional[str] = None) -> dict:
    """ Insert or update config, and insert on history table each new update"""
    db = boto3.resource("dynamodb")
    table = db.Table("ApiExtractorConfig")
    history_table = db.Table("ApiExtractorConfigHistory")
    
    data = {
        **body,
        "id": id if id else uuid4().hex
    }

    api_config = ApiConfig(**data).dict()

    table.put_item(Item=api_config)

    # insert on history table
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history_table.put_item(
        Item={**api_config, "updated_at": now, "api_key": api_key}
    )

    return api_config


def remove_config(id: str, api_key: str):
    db = boto3.resource("dynamodb")
    table = db.Table("ApiExtractorConfig")
    history_table = db.Table("ApiExtractorConfigHistory")

    config = get_api_config(id)["Item"]
    table.delete_item(Key={"id": id})

    # insert on history table
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history_table.put_item(
        Item={**config, "updated_at": now, "delete": "true", "api_key": api_key}
    )


# API KEYS SECRET

def get_api_key_name(key_value: str) -> Union[str, None]:
    client = boto3.client("secretsmanager")
    secret = client.get_secret_value(SecretId="api-extractor-config/apikeys")
    api_keys = json.loads(secret.get("SecretString"))

    found = [k[0] for k in api_keys.items() if k[1] == key_value]
    return found[0] if len(found) > 0 else None


def add_or_update_api_key(name: str, value: str):
    client = boto3.client("secretsmanager")
    secret = client.get_secret_value(SecretId="api-extractor-config/apikeys")
    api_keys = json.loads(secret.get("SecretString"))

    api_keys.update({name: value})
    client.update_secret(
        SecretId="api-extractor-config/apikeys",
        SecretString=json.dumps(api_keys)
    )

    return value


def remove_api_key(name: str):
    client = boto3.client("secretsmanager")
    secret = client.get_secret_value(SecretId="api-extractor-config/apikeys")
    api_keys = json.loads(secret.get("SecretString"))

    del api_keys[name]

    client.update_secret(
        SecretId="api-extractor-config/apikeys",
        SecretString=json.dumps(api_keys)
    )