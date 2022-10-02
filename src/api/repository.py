from typing import Optional
from datetime import datetime
from uuid import uuid4

import boto3
from boto3.dynamodb.conditions import Key

from src.api.schemas import ApiConfig


def list_api_configs():
    db = boto3.resource("dynamodb")
    table = db.Table("ApiExtractorConfig")
    resp = table.scan()
    return resp


def list_api_config_history(id: str, updated_after_that: str):
    db = boto3.resource("dynamodb")
    table = db.Table("ApiExtractorConfigHistory")

    params = {
        "KeyConditionExpression": Key("id").eq(id),
        "Limit": 50,
    }

    if updated_after_that:
        params["ExclusiveStartKey"] = {"id": id, "updated_at": updated_after_that}

    return table.query(**params)


def get_api_config(id: str):
    db = boto3.resource("dynamodb")
    table = db.Table("ApiExtractorConfig")
    return table.get_item(Key={"id": id})


def insert_config(body: dict, id: Optional[str] = None):
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
    history_table.put_item(Item={**api_config, "updated_at": now})

    return api_config


def remove_config(id: str):
    db = boto3.resource("dynamodb")
    table = db.Table("ApiExtractorConfig")
    history_table = db.Table("ApiExtractorConfigHistory")

    config = get_api_config(id)["Item"]
    table.delete_item(Key={"id": id})

    # insert on history table
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history_table.put_item(Item={**config, "updated_at": now, "delete": "true"})
