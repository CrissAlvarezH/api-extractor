from typing import Optional

from pydantic import ValidationError

from .utils import Response
from .repository import get_api_config, list_api_config_history, list_api_configs, insert_config, remove_config


def get_configs(id: Optional[str] = None):
    if id:
        resp = get_api_config(id)
        return Response(resp["Item"])
    else:
        resp = list_api_configs()
        return Response(resp["Items"])


def create_config(body: dict):
    try:
        config = insert_config(body)
        return Response(config)
    except ValidationError as e:
        errors = str(e).split("\n")
        return Response({"error": errors}, status=400)


def update_config(id: str, body: dict):
    config = get_api_config(id)
    if "Item" not in config:
        return Response({"error": "Not found"}, status=404)

    try:
        config = insert_config(body, id)
        return Response(config)
    except ValidationError as e:
        errors = str(e).split("\n")
        return Response({"error": errors}, status=400)


def get_config_history(id: str, last_updated: Optional[str] = None):
    resp = list_api_config_history(id, last_updated)
    return Response(resp)


def delete_config(id: str):
    config = get_api_config(id)
    if "Item" not in config:
        return Response({"error": "Not found"}, status=404)

    remove_config(id)
    return Response()