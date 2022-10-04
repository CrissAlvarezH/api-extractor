from typing import List, Optional

from pydantic import BaseModel


class RefreshTokenEndpoint(BaseModel):
    url: str
    query_params: Optional[dict]
    body: Optional[dict]


class ApiAuth(BaseModel):
    refresh_token_endpoint: RefreshTokenEndpoint
    token_key: str
    access_token: str
    

class EndpointConsumer(BaseModel):
    path: str
    s3_destiny: str
    data_schema: Optional[dict]


class ApiConfig(BaseModel):
    id: str
    name: str
    domain: str
    auth: ApiAuth
    endpoints: List[EndpointConsumer]
