import logging
import re
from typing import List, Union, Optional

from requests import request

from src.common.repository import get_api_config, list_api_configs
from src.common.schemas import ApiAuth, ApiConfig, Extraction


LOG = logging.getLogger("handler")


def get_configs(event) -> List[ApiConfig]:
    """ Return configs to execute 
    
    return config that coming on event on extractor_config_api key
    otherwise return all configs
    """
    config = []
    config_id = event.get("extractor_config_id")
    if config_id:
        config = get_api_config(config_id)
        if not config:
            LOG.error(f"config {config_id} does not exists")
            return
            
        configs = [config]
    else:
        # return all configs
        configs = list_api_configs()["Items"]

    return [ApiConfig(c) for c in configs]


def extract_from_json(data: dict, dot_syntax: str) -> str:
    """ Extract value from 'data' using 'dot_syntax' has json path 
    
    for instance:
    'dot_syntax' is like 'user.account.number'
    'data' is {"user": {"account": {"number": "23455"}}}
    and return value must be "23455"
    """
    temp = None
    for key in dot_syntax.split("."):
        if temp is None:
            temp = data.get(key)
            continue

        if key not in temp.keys():
            return None

        temp = temp.get(key)

    return temp


def evaluate_expression(data: dict, expression: str) -> bool:
    """ Evaluate expression over data
    
    Expression structure are
        <json_dot_syntax> <operator> <json_dot_syntax>
        or just 
        <json_dot_syntax>
        without any operator

    for example: 
        info.total_pages > info.current_page
        info.more_records
    """
    # TODO
    pass


class ReferenceHelper:
    """ Retrieve value from secret, db u other variable
    
    Values can be declared like 
        ${secret::value} ${last::value} ${self::auth.access_token}
    secret:: mean that the value is on secret manager aws
    last:: mean that the value is on the last record fetched
    access_token is just the token got on auth request

    Default value is declared after a comma, like: ${last::name, default}
    """
    _config: ApiConfig

    def __init__(self, config: ApiConfig):
        self._config = config

    def _get_from_secret(self, ref: str) -> Union[str, None]:
        # TODO get secret value
        pass

    def _get_from_last(self, ref: str, context: dict) -> Union[str, None]:
        """ Retrieve from the last record fetched by this extraction"""
        extraction_id = context.get("extraction_id")
        # TODO get ref value
        pass

    def _get_from_self(self, ref: str) -> Union[str, None]:
        return extract_from_json(self._config.dict(), ref)

    def _retrieve_reference_value(
        self, text: str, context: Optional[dict] = None
    ) -> str:
        # Extract reference params with syntax ${from::value, default}
        pattern = re.compile("(\${+[A-Za-z0-9 ,.;:/_-]+})")
        refs = pattern.findall(text)

        for ref in refs:
            # remove ${ and } from ref ex: ${self::auth, def} -> self::auth.token, def
            inside = ref[2:-1]  

            # get expression and default value
            if "," in inside:
                expression, default = inside.split(",")
                default = default.strip()
            else:
                expression = inside
                default = None

            retrieve_from, ref_value = expression.strip().split("::")

            if retrieve_from == "secret":
                value = self._get_from_secret(ref_value)
            elif retrieve_from == "self":
                value = self._get_from_self(ref_value)
            elif retrieve_from == "last":
                value = self._get_from_last(value, context)
            
            if value is None:
                value = default

            # replace ref by retrieved value
            text = text.replace(ref, value)

        return text

    def replace(self, json: dict, context: Optional[dict] = None) -> dict:
        """ replace all ${} references by its value in json """
        for key, value in json.items():
            if isinstance(value, dict):
                self.replace(value, context)
            elif isinstance(value, str):
                json[key] = self._retrieve_reference_value(json[key], context)
        return json


class ApiExtractorService:
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

        access_token = extract_from_json(
            resp, auth.refresh_token.response_token_key)

        # set access token in config and on secret if is a reference secret::
        auth.access_token = access_token
        # TODO update token on db or secret

        return access_token
    
    def extract(self, extraction: Extraction) -> dict:
        # TODO execute extraction
        if extraction.pagination == "sequential":
            page = int(extraction.pagination.parameters.start_from)
            continue_to_next = True
            while continue_to_next:
                method = extraction.endpoint.method or "get"
                resp = request(
                    method,
                    extraction.endpoint.url,
                    params={
                        **extraction.endpoint.query_params,
                        extraction.pagination.parameters.param_name: page
                    },
                    data=extraction.endpoint.body,
                    headers=extraction.endpoint.headers
                )

                page += 1
                continue_to_next = evaluate_expression(
                    data=resp,
                    expression=extraction.pagination.parameters.there_are_more_pages
                )


    def run(self):
        access_token = self.refresh_token(self._config.auth)

        for extraction_config in self._config.extractions:
            filled_extraction_data = self._references.replace(
                extraction_config.dict(), 
                context={"extraction_id": extraction_config.id}
            )

            extraction = Extraction(**filled_extraction_data)

            

            


def handler(event, context):
    print("Execution, event: ", event, " context: ", context)

    configs = get_configs(event)

    for config in configs:
        # TODO run ApiExtractorService

        # TODO convert data to csv

        # TODO send to s3
        pass
