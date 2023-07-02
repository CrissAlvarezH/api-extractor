from typing import Tuple, Optional, List
import json
import math
import os

from dotenv import load_dotenv

from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.applications import Starlette
from starlette.routing import Route


load_dotenv()


def validate_auth_token(request: Request) -> Tuple[Optional[str], Optional[JSONResponse]]:
    token = request.headers.get("Authorization", " ").split(" ")[1].strip()
    if token != os.environ.get("FAKE_API_TOKEN", ""):
        return None, JSONResponse({"details": "Error token"})
    return token, None


def load_data():
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, "data.json")) as f:
        data = json.loads(f.read())
    return data

def map_data_to_list(data: List[dict]):
    """ exclude retrieve data """
    def mapper(item: dict) -> dict:
        del item["retrieve_data"]
        return item
    return [mapper(i) for i in data]


async def payments(request: Request):
    _, error_res = validate_auth_token(request)
    if error_res:
        return error_res

    data = map_data_to_list(load_data())

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


async def payments_without_pagination(request: Request):
    _, error_res = validate_auth_token(request)
    if error_res:
        return error_res

    data = map_data_to_list(load_data())

    ordering = request.query_params.get("ordering")
    if ordering:
        data.sort(key=lambda i: i.get(ordering))

    # important: index start from 1, not 0 that's what it is dismiss in 1
    index_from = int(request.query_params.get("from", 1)) - 1
    limit = int(request.query_params.get("limit", 20))
    offset = limit + index_from

    page_data = data[index_from:offset]

    if len(page_data) > 0:
        return JSONResponse({"data": page_data})
    return Response(status_code=status.HTTP_204_NO_CONTENT)

async def retrieve_payment(request: Request):
    _, error_res = validate_auth_token(request)
    if error_res:
        return error_res

    id = request.path_params.get("id")
    data = load_data()

    filtered = [i for i in data if i["id"] == id]

    if len(filtered) == 0:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return JSONResponse(filtered[0])
    

def auth(request: Request):
    if request.query_params.get("secret") != os.environ.get("FAKE_API_SECRET_TO_GET_TOKEN"):
        return JSONResponse({"details": "error secret"})

    return JSONResponse({"access_token": os.environ.get("FAKE_API_TOKEN")})


app = Starlette(debug=True, routes=[
    Route("/auth", auth, methods=["POST"]),
    Route("/payments", payments),
    Route("/payments/{id}", retrieve_payment),
    Route("/payments-without-pagination", payments_without_pagination),
])
