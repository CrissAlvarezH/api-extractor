import json

from .utils import Response
from .routes import delete_config, get_config_history, get_configs, create_config, update_config


def handler(event, context):
    method, path = event.get("routeKey").split(" ")
    path_params = event.get("pathParameters", {})
    query_params = event.get("queryStringParameters", {})
    body = json.loads(event["body"]) if "body" in event else {}

    response = Response({"error": "invalid path"}, status=400)

    if path in ("/config", "/config/{id}"):
        if method == "GET":
            response = get_configs(path_params.get("id"))
        elif method == "POST":
            response = create_config(body)
        elif method == "PUT":
            response = update_config(path_params.get("id"), body)
        elif method == "DELETE":
            response = delete_config(path_params.get("id"))

    elif path == "/config/{id}/history":
        response = get_config_history(
            path_params.get("id"), query_params.get("last_updated_at"))

    return {
        "statusCode": response.status,
        "body": json.dumps(response.body) if response.body else None,
        "headers": {
            "Content-Type": "application/json"
        }
    }
