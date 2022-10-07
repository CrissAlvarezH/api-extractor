from typing import Optional, Union
from datetime import datetime
from uuid import uuid4

from boto3.dynamodb.conditions import Key

from src.common.aws import config_db_table, execution_logs_table
from src.extractor.utils import dumps_json

from .schemas import ApiConfig, Extraction

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


def put_config(
    body: dict,
    id: Optional[str] = None,
    api_key: Optional[str] = None
) -> dict:
    """ Insert or update config, and insert on history table each new update"""
    table, history_table = config_db_table()
    
    data = {
        **body,
        "id": id if id else uuid4().hex
    }

    api_config = ApiConfig(**data).dict()

    extractions_in = api_config.get("extractions", [])

    if id:
        # validate extractions exists in db
        api_config_in_db = get_api_config(id)["Item"]
        def extraction_exists(extraction_id: str) -> bool:
            found = [e for e in api_config_in_db.get("extractions") 
                     if e.get("id") == extraction_id]
            return len(found) > 0

        for extraction in extractions_in:
            if extraction.get("id") and not extraction_exists(extraction.get("id")):
                raise ValueError(f"Extraction {extraction.get('id')} does't exists")

    # add id for new extractions
    for extraction in extractions_in:
        if not extraction.get("id"):
            extraction["id"] = uuid4().hex

    table.put_item(Item=api_config)

    # insert on history table
    if api_key:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history_table.put_item(
            Item={**api_config, "updated_at": now, "api_key": api_key}
        )

    return api_config


def update_access_token(config_id: str, access_token: str):
    config_data = get_api_config(config_id)["Item"]
    config = ApiConfig(**config_data)
    config.auth.access_token = access_token

    put_config(body=config.dict(), id=config_id)


def remove_config(id: str, api_key: str):
    table, history_table = config_db_table()

    config = get_api_config(id)["Item"]
    table.delete_item(Key={"id": id})

    # insert on history table
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history_table.put_item(
        Item={**config, "updated_at": now, "delete": "true", "api_key": api_key}
    )


# EXTRACTOR LOGS

def insert_execution_log(
    extraction: Extraction,
    config: ApiConfig,
    destiny: str,
    last: dict,
    data_inserted_len: int,
    error: Optional[str] = None
):
    table = execution_logs_table()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    table.put_item(Item={
        "extraction_name": extraction.name,
        "extraction_id": str(extraction.id),
        "config_id": str(config.id),
        "config_name": config.name,
        "data_inserted_len": str(data_inserted_len),
        "destiny": destiny,
        "last": dumps_json(last),
        "success": "true" if error is None else "false",
        "error": error,
        "created_at": now
    })    


def list_extraction_execution_logs(
    id: Optional[str] = None,
    limit: int = 50,
    created_after_that: Optional[str] = None,
) -> dict:
    table = execution_logs_table()

    params = {
        "ScanIndexForward": False,
        "Limit": limit,
    }

    if id:
        params["KeyConditionExpression"] = Key("extraction_id").eq(id)

    if created_after_that:
        params["ExclusiveStartKey"] = {
            "extraction_id": id,
            "created_at": created_after_that
        }

    return table.query(**params)


def get_last_execution_log(extraction_id: str) -> Union[dict, None]:
    resp = list_extraction_execution_logs(extraction_id, limit=1)
    items = resp.get("Items", [])
    return items[0] if len(items) > 0 else None
    