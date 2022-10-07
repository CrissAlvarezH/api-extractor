import logging
from datetime import datetime
from typing import List
from io import StringIO

import pandas
import requests
import boto3
from requests import request

from src.common.repository import insert_execution_log, update_access_token
from src.common.schemas import ApiAuth, ApiConfig, Extraction

from .utils import extract_from_json, evaluate_expression
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
                if isinstance(value_schema, dict):
                    iterate_schema(value_schema, data.get(key_schema), result)
                else:
                    result[value_schema] = data.get(key_schema)  

        result = []
        for item in data:
            result_item = {}
            iterate_schema(self._extraction.data_schema, item, result_item)
            result.append(result_item)

        return result
    
    def run(self) -> List[dict]:
        LOG.info(f'run extraction: {self._extraction}')
        all_data = []

        for page in self.paginate():
            all_data.extend(page) 

        if self._extraction.data_schema:
            all_data = self.apply_schema(all_data)

        return all_data


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

    def send_to_s3(self, df, extraction: Extraction):
        buffer = StringIO()
        df.to_csv(buffer, index=False)
        s3 = boto3.resource("s3")

        filename = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S") + ".csv"
        file_path = extraction.s3_destiny.folder + filename
        s3.Object(
            extraction.s3_destiny.bucket,
            file_path,
        ).put(Body=buffer.getvalue())

        return f"s3://{extraction.s3_destiny.bucket}{file_path}"

    def run(self):
        for extraction_config in self._config.extractions:
            data = []
            error = None
            s3_path = None

            try:
                self.refresh_token(self._config.auth)

                # replace references on extraction
                filled_extraction_data = self._references.replace(
                    extraction_config.dict(), 
                    context={"extraction_id": extraction_config.id}
                )
                extraction = Extraction(**filled_extraction_data)

                data = EndpointExtractorService(extraction).run()

                df = self.convert_to_csv(data)

                s3_path = self.send_to_s3(df, extraction)

                LOG.info(f"successfully extraction {extraction} loaded on {s3_path}")
            except Exception as e:
                error = str(e)
                LOG.error(f"extraction {extraction_config.id}, exc: {str(e)}")
                LOG.exception(e)

            # Insert logs
            last_item = data[len(data) - 1] if data else None
            insert_execution_log(
                extraction=extraction_config,
                config=self._config,
                data_inserted_len=len(data) if data else 0,
                last=last_item,
                destiny=s3_path,
                error=error,
            )
