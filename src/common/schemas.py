from typing import List, Optional, Union

from pydantic import BaseModel, Field, validator

from src.common.constants import DESTINY_BUCKET_NAME


class Endpoint(BaseModel):
    url: str
    method: Optional[str]
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
    type: str = Field()
    parameters: Union[SequentialPaginationParams, LinkPaginationParams]


class S3Path(BaseModel):
    bucket: Optional[str] = Field(DESTINY_BUCKET_NAME)
    folder: Optional[str] = Field("")
    filename: Optional[str] = Field("{timestamp}")


class OutputParams(BaseModel):
    csv_separator: Optional[str] = Field(",")


class Transformation(BaseModel):
    action: str
    priority: Optional[int] = Field(0, gt=-1)
    on: Optional[Union[List[str], str]] = Field("__all__")
    params: Optional[dict]
    new_column_prefix: Optional[str] = Field()


class Extraction(BaseModel):
    id: Optional[str]
    name: str
    endpoint: Endpoint
    data_key: Optional[str]
    transformations: Optional[List[Transformation]] = Field([])
    output_params: Optional[OutputParams] = Field(OutputParams())
    pagination: Pagination
    format: Optional[str] = Field("csv")
    s3_destiny: S3Path = Field(S3Path())
    data_schema: Optional[dict]

    @validator("format")
    def validate_format(cls, v):
        valid_formats = ["csv", "json"]
        if v not in valid_formats:
            raise ValueError(f"Invalid format, options: {valid_formats}")
        return v

    def __str__(self) -> str:
        return f"{self.id}: {self.name}"


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

    def __str__(self) -> str:
        return f"{self.id}: {self.name}"
