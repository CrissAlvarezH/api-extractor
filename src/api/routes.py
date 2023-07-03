import json
import secrets
import logging
from typing import Optional

import boto3
from pydantic import ValidationError

from src.common.constants import API_EXTRACTOR_FUNCTION_NAME
from src.common.secrets import add_or_update_api_key, remove_api_key
from src.common.repository import (
    get_api_config, list_api_config_history, list_api_configs, 
    list_extraction_execution_logs, put_config, remove_config
)

from .utils import Response

LOG = logging.getLogger("api-routes")

# API CONFIGS

def get_configs(id: Optional[str] = None):
    if id:
        resp = get_api_config(id)
        if "Item" not in resp:
            return Response({"error": "Not found"}, 404)
        return Response(resp["Item"])
    else:
        resp = list_api_configs()
        return Response(resp)


def create_config(body: dict, api_key: str):
    try:
        config = put_config(body, api_key=api_key)
        return Response(config)
    except ValidationError as e:
        errors = str(e).split("\n")
        LOG.error(f"create config: {e}")
        return Response({"error": errors}, status=400)


def update_config(id: str, body: dict, api_key: str):
    config = get_api_config(id)
    if "Item" not in config:
        return Response({"error": "Not found"}, status=404)

    try:
        config = put_config(body, id, api_key)
        return Response(config)
    except ValidationError as e:
        errors = str(e).split("\n")
        return Response({"error": errors}, status=400)
    except ValueError as e:
        return Response({"error": str(e)}, status=400)


def get_config_history(id: str, last_updated: Optional[str] = None):
    resp = list_api_config_history(id, last_updated)
    return Response(resp)


def delete_config(id: str, api_key: str):
    config = get_api_config(id)
    if "Item" not in config:
        return Response({"error": "Not found"}, status=404)

    remove_config(id, api_key)
    return Response()


def invoke_api_extractor(id: str):
    if "Item" not in get_api_config(id):
        return Response({"error": "Not found"}, 404)

    client = boto3.client("lambda")
    resp = client.invoke_async(
        FunctionName=API_EXTRACTOR_FUNCTION_NAME,
        InvokeArgs=bytes(json.dumps({"extractor_config_id": id}), encoding="utf8")
    )
    return Response(resp)


def get_extractor_execution_logs(extractor_id: str):
    resp = list_extraction_execution_logs(extractor_id)
    return Response(resp)


# API KEYS

def generate_api_key(key_on_request: str, name: str):
    if name is None:
        return Response({"error": "name is required"}, 400)
    if key_on_request not in ("rootkey", name):
        # if not is root key or key owner 
        return Response({"error": "Not authorized"}, 403)

    api_key = secrets.token_hex(nbytes=27)
    add_or_update_api_key(name, api_key)
    return Response({"name": name, "api_key": api_key})


def delete_api_key(key_on_request: str, name: str):
    if key_on_request not in ("rootkey", name):
        # if not is root key or key owner 
        return Response({"error": "Not authorized"}, 403)
    
    if name == "rootkey":
        return Response(
            {"error": "rootkey can't be deleted by api"},
            status=403
        )

    remove_api_key(name)
    return Response()
