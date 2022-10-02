from typing import List, Optional

from pydantic import BaseModel


class ApiAuth(BaseModel):
    access_token: str
    refresh_token: str
    

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
