import json
from typing import Optional, Union
from datetime import datetime
from uuid import uuid4

from boto3.dynamodb.conditions import Key

from src.api.constants import API_KEYS_SECRET_NAME

from .schemas import ApiConfig
from .utils import api_keys_secrets, config_db_table

# API CONFIG 

def list_api_configs() -> dict:
    table, _ = config_db_table()
    resp = table.scan()
    return resp


def list_api_config_history(id: str, updated_after_that: str) -> dict:
    _, history_table = config_db_table()

    params = {
        "KeyConditionExpression": Key("id").eq(id),
        "Limit": 50,
    }

    if updated_after_that:
        params["ExclusiveStartKey"] = {"id": id, "updated_at": updated_after_that}

    return history_table.query(**params)


def get_api_config(id: str) -> dict:
    table, _ = config_db_table()
    return table.get_item(Key={"id": id})


def insert_config(api_key: str, body: dict, id: Optional[str] = None) -> dict:
    """ Insert or update config, and insert on history table each new update"""
    table, history_table = config_db_table()
    
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
    table, history_table = config_db_table()

    config = get_api_config(id)["Item"]
    table.delete_item(Key={"id": id})

    # insert on history table
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history_table.put_item(
        Item={**config, "updated_at": now, "delete": "true", "api_key": api_key}
    )


# API KEYS SECRET

def get_api_key_name(key_value: str) -> Union[str, None]:
    _, api_keys = api_keys_secrets()

    found = [k[0] for k in api_keys.items() if k[1] == key_value]
    return found[0] if len(found) > 0 else None


def add_or_update_api_key(name: str, value: str):
    client, api_keys = api_keys_secrets()
    api_keys.update({name: value})
    client.update_secret(
        SecretId=API_KEYS_SECRET_NAME,
        SecretString=json.dumps(api_keys)
    )

    return value


def remove_api_key(name: str):
    client, api_keys = api_keys_secrets()

    del api_keys[name]

    client.update_secret(
        SecretId=API_KEYS_SECRET_NAME,
        SecretString=json.dumps(api_keys)
    )