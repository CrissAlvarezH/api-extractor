from typing import List, Optional, Union

from pydantic import BaseModel, Field, validator, root_validator

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
    step: str = "1"
    there_are_more_pages: Optional[str]
    continue_while_status_code_is: Optional[str]
    stop_when_response_body_is_empty: Optional[bool] = False

    @root_validator
    def validate_continue_conditions_are_not_set_both(cls, values):
        if (
            values.get("there_are_more_pages") is not None
            and values.get("continue_while_status_code_is") is not None
        ):
            raise ValueError(
                "'there_are_more_pages' and 'continue_while_status_code_is' "
                "cannot are settled both"
            )

        return values


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


class MappingFetch(BaseModel):
    endpoint: Endpoint
    prefix: Optional[str] = Field("details__")
    data_schema: Optional[dict]


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
    mapping_fetch: Optional[MappingFetch] = Field(None)

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
        extraction_ids = [e.id for e in v if e.id is not None and len(e.id) > 0]
        match = [_id for _id in extraction_ids if _id == extraction_ids]
        if len(match) == 2:
            raise ValueError("There are two extraction with same id")
        return v

    def __str__(self) -> str:
        return f"{self.id}: {self.name}"
