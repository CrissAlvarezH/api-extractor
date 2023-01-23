import json
import math
import os

from dotenv import load_dotenv

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.applications import Starlette
from starlette.routing import Route


load_dotenv()


async def data(request: Request):
    token = request.headers.get("Authorization", " ").split(" ")[1]
    if token != os.environ.get("FAKE_API_TOKEN", ""):
        return JSONResponse({"details": "Error token"})

    # load data
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, "data.json")) as f:
        data = json.loads(f.read())

    ordering = request.query_params.get("ordering")
    if ordering:
        data.sort(key=lambda i: i.get(ordering))

    # create pagination
    per_page = int(request.query_params.get("per_page", 10))
    page = int(request.query_params.get("page", 1))
    total_pages = (len(data) / per_page)
    data_from = per_page * (page - 1)
    data_to = per_page + data_from
    page_data = data[data_from:data_to]
    response = {
        "result": page_data,
        "pagination": {
            "current_page": page,
            "on_page": len(page_data),
            "total_items": len(data),
            "total_pages": math.ceil(total_pages),
            "more_records": page < total_pages
        }
    }

    return JSONResponse(response)


def auth(request: Request):
    if request.query_params.get("secret") != os.environ.get("FAKE_API_SECRET_TO_GET_TOKEN"):
        return JSONResponse({"details": "error secret"})

    return JSONResponse({"access_token": os.environ.get("FAKE_API_TOKEN")})


app = Starlette(debug=True, routes=[
    Route("/auth", auth, methods=["POST"]),
    Route("/data", data),
])
