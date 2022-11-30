import logging
import json
from datetime import datetime
from typing import List, Optional
from io import StringIO

import pandas
import requests
import boto3
from requests import request

from src.common.repository import (
    get_last_item_from_last_time, insert_execution_log, update_access_token
)
from src.common.schemas import ApiAuth, ApiConfig, Extraction

from .utils import extract_from_json, evaluate_expression, replace_decimal
from .helpers import ReferenceHelper


LOG = logging.getLogger("services")
LOG.setLevel(logging.INFO)


class EndpointExtractorService:
    _extraction: Extraction

    def __init__(self, extraction: Extraction):
        self._extraction = extraction

    def paginate(self):
        page = int(self._extraction.pagination.parameters.start_from)
        url = self._extraction.endpoint.url
        continue_to_next = True
        while continue_to_next:
            query_params = self._extraction.endpoint.query_params
            if self._extraction.pagination.type == "sequential":
                query_params[self._extraction.pagination.parameters.param_name] = page

            resp = request(
                self._extraction.endpoint.method or "get",
                url,
                params=query_params,
                data=self._extraction.endpoint.body,
                headers=self._extraction.endpoint.headers
            )
            
            if resp.status_code > 299 or resp.status_code < 200:
                raise Exception(
                    f"extraction {self._extraction.id} return status "
                    f"code: {resp.status_code}, body: {resp.text}")
            
            response_body = resp.json()

            if self._extraction.data_key:
                data = response_body.get(self._extraction.data_key)
            else:
                data = response_body

            if data is None:
                data = []
            elif isinstance(data, dict):
                data = [data] # covert to list before append to all_data

            yield data

            if self._extraction.pagination.type == "sequential":
                page += 1
                continue_to_next = evaluate_expression(
                    data=response_body,
                    expression=self._extraction.pagination.parameters.there_are_more_pages
                ) 

            elif self._extraction.pagination.type == "link":
                url = extract_from_json(
                    response_body,
                    self._extraction.pagination.parameters.next_link
                )
                continue_to_next = url is not None

    def apply_schema(self, data: List[dict]) -> List[dict]:
        def iterate_schema(schema, data, result):
            for key_schema, value_schema in schema.items():
                if data is None:
                    result[value_schema] = None
                elif isinstance(value_schema, dict):
                    iterate_schema(value_schema, data.get(key_schema), result)
                else:
                    result[value_schema] = data.get(key_schema)  

        result = []
        for item in data:
            result_item = {}
            iterate_schema(self._extraction.data_schema, item, result_item)
            result.append(result_item)

        return result
    
    def remove_first_if_last_is_equal(
        self, data: List[dict], last: Optional[dict] = None
    ) -> List[dict]:
        """ remove first item if is the same that the last item of the last time """
        first_item = data[0] if data else None
        if first_item and last and replace_decimal(first_item) == last:
            LOG.info("the first item is the same than the last, remove it")
            return data[1:]
        return data

    def run(self) -> List[dict]:
        LOG.info(f'run extraction: {self._extraction}')
        data = []

        for page in self.paginate():
            data.extend(page) 

        previous_last_item = get_last_item_from_last_time(self._extraction.id)
        if len(data) == 0:
            return [], previous_last_item

        current_last_item = data[len(data) - 1] 
        data = self.remove_first_if_last_is_equal(data, previous_last_item)

        if self._extraction.data_schema:
            data = self.apply_schema(data)

        return data, current_last_item


class ApiService:
    _config: ApiConfig
    _references: ReferenceHelper

    def __init__(self, config: ApiConfig):
        self._config = config
        self._references = ReferenceHelper(config)

    def refresh_token(self, auth_config: ApiAuth) -> str:
        # replace all references ${} to its raw value from auth_config
        auth = ApiAuth(**self._references.replace(auth_config.dict()))

        resp = requests.post(
            auth.refresh_token.endpoint.url,
            params=auth.refresh_token.endpoint.query_params,
            data=auth.refresh_token.endpoint.body,
            headers=auth.refresh_token.endpoint.headers
        )
        response_body = resp.json()

        access_token = extract_from_json(
            response_body, auth.refresh_token.response_token_key)
        
        if not access_token:
            raise ValueError(f"access token refreshed is invalid,  resp: {response_body}")

        # set access token in config and on secret if is a reference secret::
        auth.access_token = access_token
        self._config.auth = auth  # update reference to auth values
        update_access_token(self._config.id, access_token)

    def convert_to_csv(self, data: dict):
        df = pandas.DataFrame(data)
        df["ext__timestamp"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")
        return df

    def send_to_s3(self, data, extraction: Extraction):
        if extraction.format == "csv":
            buffer = StringIO()
            data.to_csv(buffer, index=False)
            file_body = buffer.getvalue()
        elif extraction.format == "json":
            file_body = bytes(json.dumps(data).encode("UTF-8"))

        file_ext = "." + extraction.format
        filename = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S") + file_ext
        file_path = extraction.s3_destiny.folder + filename
        s3 = boto3.resource("s3")
        s3.Object(
            extraction.s3_destiny.bucket,
            file_path,
        ).put(Body=file_body)

        return f"s3://{extraction.s3_destiny.bucket}/{file_path}"

    def run(self):
        LOG.info(f"start to execute api config: {self._config}")
        for extraction_config in self._config.extractions:
            data = []
            data_length = 0
            last_item = None
            error = None
            s3_path = None

            try:
                if self._config.auth.refresh_token:
                    self.refresh_token(self._config.auth)

                # replace references on extraction
                filled_extraction_data = self._references.replace(
                    extraction_config.dict(), 
                    context={"extraction_id": extraction_config.id}
                )
                extraction = Extraction(**filled_extraction_data)

                data, last_item = EndpointExtractorService(extraction).run()
                data_length = len(data)

                if data_length > 0:
                    if extraction.format == "csv":
                        data = self.convert_to_csv(data)

                    s3_path = self.send_to_s3(data, extraction)
                    LOG.info(f"successfully extraction {extraction} loaded on {s3_path}")
                else:
                    LOG.warning(f"data is empty on extraction {extraction}")

            except Exception as e:
                error = str(e)
                LOG.error(f"extraction {extraction_config.id}, exc: {str(e)}")
                LOG.exception(e)

            insert_execution_log(
                extraction=extraction_config,
                config=self._config,
                data_inserted_len=data_length,
                last=last_item,
                destiny=s3_path,
                error=error,
            )
