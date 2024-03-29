import re
import logging
from datetime import datetime
from typing import List, Optional, Union, Tuple
from io import StringIO

import pandas
import requests
import boto3
from requests import request

from src.common.repository import (
    get_last_item_from_last_time, insert_execution_log, update_access_token, 
    get_last_execution_log
)
from src.common.schemas import ApiAuth, ApiConfig, Extraction, Transformation, Endpoint
from src.common.aws import extractor_secrets

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
        step = int(self._extraction.pagination.parameters.step)
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
            
            if len(resp.text.strip()) == 0:
                data = []
            else:
                response_body = resp.json()

                if self._extraction.data_key:
                    data = response_body.get(self._extraction.data_key)
                else:
                    data = response_body

            if data is None:
                data = []
            elif isinstance(data, dict):
                data = [data] # covert to list before append to all_data
            
            LOG.info(f"extract {len(data)} items, from: {url}, query: {query_params}")
            if len(data) == 0:
                LOG.warning(f"Endpoint return empty data: {resp.text}")

            yield data

            if self._extraction.pagination.type == "sequential":
                page += step
                if (
                    len(resp.text.strip()) == 0
                    and self._extraction.pagination.parameters.stop_when_response_body_is_empty
                ):
                    continue_to_next = False
                    LOG.info("stop because response is empty")
                elif self._extraction.pagination.parameters.there_are_more_pages:
                    continue_to_next = evaluate_expression(
                        data=response_body,
                        expression=self._extraction.pagination.parameters.there_are_more_pages
                    ) 
                elif self._extraction.pagination.parameters.continue_while_status_code_is:
                    expected_status = (
                        self._extraction.pagination
                        .parameters
                        .continue_while_status_code_is
                    )

                    continue_to_next = str(resp.status_code) == str(expected_status)
                    LOG.info(f"Pagination res: {continue_to_next}, status code: {resp.status_code}")

            elif self._extraction.pagination.type == "link":
                url = extract_from_json(
                    response_body,
                    self._extraction.pagination.parameters.next_link
                )
                continue_to_next = url is not None

    def apply_mapping_fetch(self, data: List[dict]) -> List[dict]:
        for item in data:
            endpoint = self._extraction.mapping_fetch.endpoint
            endpoint = Endpoint(**ReferenceHelper.replace(
                endpoint.dict(), context={"extracted_item": item}))

            resp = request(
                endpoint.method or "get",
                endpoint.url,
                params=endpoint.query_params,
                data=endpoint.body,
                headers=endpoint.headers
            )

            if len(resp.text.strip()) == 0:
                LOG.warning(f"mapping fetch: EMPTY RESPONSE, for: {item}")
                continue
            
            result = self.apply_schema(
                self._extraction.mapping_fetch.data_schema,
                data=[resp.json()],
                prefix=self._extraction.mapping_fetch.prefix
            )[0]

            # add data from endpoint to item
            item.update(result)
             
        return data

    @classmethod
    def apply_schema(cls, data_schema: dict, data: List[dict], prefix: str = "") -> List[dict]:
        def iterate_schema(schema, data, result):
            for key_schema, value_schema in schema.items():
                if data is None:
                    result[prefix + value_schema] = None
                elif isinstance(value_schema, dict):
                    iterate_schema(value_schema, data.get(key_schema), result)
                else:
                    result[prefix + value_schema] = data.get(key_schema)  

        result = []
        for item in data:
            result_item = {}
            iterate_schema(data_schema, item, result_item)
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

    def run(self) -> Tuple[List[dict], Union[dict, None]]:
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
            data = self.apply_schema(self._extraction.data_schema, data)
        
        if self._extraction.mapping_fetch:
            data = self.apply_mapping_fetch(data)

        return data, current_last_item


class ApiService:
    _config: ApiConfig
    _secrets: dict

    def __init__(self, config: ApiConfig):
        self._config = config
        _, secrets = extractor_secrets()
        self._secrets = secrets

    def refresh_token(self, auth_config: ApiAuth):
        filled_auth_refs = ReferenceHelper.replace(
            auth_config.dict(),
            context={"secret": self._secrets, "self": self._config.dict()}
        )
        auth = ApiAuth(**filled_auth_refs)

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

    def apply_transformations(self, transformations: List[Transformation], data: List[dict]) -> pandas.DataFrame:
        transform_switcher = {
            "replace": lambda series: series.str.replace(t.params["to_replace"], t.params["value"], regex=False),
            "trim": lambda series: series.str.trim(),
            "ltrim": lambda series: series.str.ltrim(),
            "rtrim": lambda series: series.str.rtrim(),
            "lower": lambda series: series.str.lower(),
            "upper": lambda series: series.str.upper(),
            "title": lambda series: series.str.title(),
            "capitalize": lambda series: series.str.capitalize(),
            "split": lambda series: series.str.split(t.params["char"]),
            "join": lambda series: series.str.join(t.params["sep"]),
            "slice": lambda series: series.str.slice(start=int(t.params["start"]), stop=int(t.params["stop"])),
        }

        df = pandas.DataFrame(data)
        transformations.sort(key=lambda x: x.priority)
        for t in transformations:
            transform = transform_switcher.get(t.action)
            if not transform:
                LOG.error(f"transform {t.action} does not exists")
                continue

            columns = list(df.columns) if t.on == "__all__" else t.on
            for column in columns:
                result = transform(df[column])
                if t.new_column_prefix:
                    column = t.new_column_prefix + column
                df[column] = result

        df["ext__timestamp"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")
        return df

    def replace_extraction_references(self, extraction: Extraction) -> Extraction:
        """ Replace references like ${secret::my_secret}, ${self::name}, etc"""

        # get last log of extraction
        last_log = get_last_execution_log(extraction.id)
        last = last_log.get("last", {}) if last_log else None
        
        filled_extraction_data = ReferenceHelper.replace(
            extraction.dict(), 
            context={
                "self": self._config.dict(),
                "last": last,
                "secret": self._secrets
            }
        )
        return Extraction(**filled_extraction_data)

    def send_to_s3(self, data: pandas.DataFrame, extraction: Extraction):
        if extraction.format == "csv":
            buffer = StringIO()
            data.to_csv(buffer, index=False, sep=extraction.output_params.csv_separator)
            file_body = buffer.getvalue()
        elif extraction.format == "json":
            buffer = StringIO()
            data.to_json(buffer)
            file_body = bytes(buffer.getvalue().encode("UTF-8"))
        else:
            raise NotImplementedError(f"format {extraction.format} is not supported")

        file_ext = "." + extraction.format
        filename = (
            extraction.s3_destiny.filename
            .format(timestamp=datetime.utcnow().strftime("%Y-%m-%d@%H-%M-%S")) 
            + file_ext
        )
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
            data_length = 0
            last_item = None
            error = None
            s3_path = None

            try:
                if self._config.auth.refresh_token:
                    self.refresh_token(self._config.auth)

                extraction = self.replace_extraction_references(extraction_config)

                data, last_item = EndpointExtractorService(extraction).run()
                data_length = len(data)

                if data_length > 0:
                    data = self.apply_transformations(extraction.transformations, data)

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
