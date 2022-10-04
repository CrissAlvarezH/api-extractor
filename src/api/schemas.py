from typing import List, Optional, Union

from pydantic import BaseModel, Field, validator


class Endpoint(BaseModel):
    url: str
    query_params: Optional[dict]
    headers: Optional[dict]
    body: Optional[dict]


class RefreshToken(BaseModel):
    endpoint: Endpoint
    response_token_key: str


class ApiAuth(BaseModel):
    refresh_token: Optional[RefreshToken]
    access_token: str
    

class SequentialPaginationParams(BaseModel):
    param_name: str
    start_from: Optional[str] = Field("1")
    there_are_more_pages: str


class LinkPaginationParams(BaseModel):
    next_link: str


class Pagination(BaseModel):
    type: str
    parameters: Union[SequentialPaginationParams, LinkPaginationParams]


class Extraction(BaseModel):
    id: Optional[str]
    name: str
    endpoint: Endpoint
    pagination: Pagination
    s3_destiny: str
    data_schema: Optional[dict]


class ApiConfig(BaseModel):
    id: str
    name: str
    auth: Optional[ApiAuth]
    extractions: List[Extraction]

    @validator("extractions")
    def validate_duplicated_extractor_ids(cls, v):
        for extraction in v:
            match = [e for e in v if e.id == extraction.id]
            if len(match) == 2:
                raise ValueError("There are two extraction with same id")
        return v
