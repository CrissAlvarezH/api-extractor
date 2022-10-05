import json

from ..common.repository import get_api_key_name
from .routes import delete_api_key, delete_config, generate_api_key, get_config_history, get_configs, create_config, invoke_api_extractor, update_config
from .utils import Response


def handler(event, context):
    method, path = event.get("routeKey").split(" ")
    authorization = event.get("headers").get("authorization")
    path_params = event.get("pathParameters", {})
    query_params = event.get("queryStringParameters", {})
    body = json.loads(event["body"]) if "body" in event else {}

    # validate api ley
    api_key_name = get_api_key_name(authorization)
    if api_key_name is None:
        return Response({"error": "Unauthorized"}, status=403).json

    response = Response({"error": "invalid path"}, status=400)

    if path in ("/config", "/config/{id}"):
        if method == "GET":
            response = get_configs(path_params.get("id"))
        elif method == "POST":
            response = create_config(body, api_key_name)
        elif method == "PUT":
            response = update_config(path_params.get("id"), body, api_key_name)
        elif method == "DELETE":
            response = delete_config(path_params.get("id"), api_key_name)

    elif path == "/config/{id}/history":
        response = get_config_history(
            path_params.get("id"), query_params.get("last_updated_at"))

    elif path == "/config/{id}/execute":
        response = invoke_api_extractor(path_params.get("id"))

    elif path in ("/api-keys", "/api-keys/{name}"):
        if method == "POST":
            response = generate_api_key(api_key_name, body.get("name"))
        elif method == "DELETE":
            response = delete_api_key(api_key_name, path_params.get("name"))
    
    elif path == "/api-keys/{name}/refresh":
        response = generate_api_key(api_key_name, path_params.get("name"))

    return response.json