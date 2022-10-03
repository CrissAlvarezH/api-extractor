import json
import secrets
from typing import Optional

import boto3
from pydantic import ValidationError

from src.api.constants import API_EXTRACTOR_FUNCTION_NAME

from .utils import Response
from .repository import add_or_update_api_key, get_api_config, list_api_config_history, list_api_configs, insert_config, remove_api_key, remove_config


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
        config = insert_config(api_key, body)
        return Response(config)
    except ValidationError as e:
        errors = str(e).split("\n")
        return Response({"error": errors}, status=400)


def update_config(id: str, body: dict, api_key: str):
    config = get_api_config(id)
    if "Item" not in config:
        return Response({"error": "Not found"}, status=404)

    try:
        config = insert_config(api_key, body, id)
        return Response(config)
    except ValidationError as e:
        errors = str(e).split("\n")
        return Response({"error": errors}, status=400)


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
        InvokeArgs=bytes(json.dumps({"id": id}), encoding="utf8")
    )
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
