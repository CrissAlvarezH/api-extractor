import re
import logging
from typing import Union, Optional

from src.common.aws import extractor_secrets
from src.common.repository import get_last_execution_log
from src.common.schemas import ApiConfig

from .utils import extract_from_json

LOG = logging.getLogger("helpers")
LOG.setLevel(logging.INFO)


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
        _, secrets = extractor_secrets()
        return secrets.get(ref)

    def _get_from_last(self, ref: str, context: dict) -> Union[str, None]:
        """ Retrieve from the last record fetched by this extraction"""
        extraction_id = context.get("extraction_id")
        last_log = get_last_execution_log(extraction_id)
        return last_log.get("last", {}).get(ref) if last_log else None

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
                value = self._get_from_last(ref_value, context)
            
            if value is None:
                value = default

            if value is None:
                raise ValueError(f"Ref {ref} return None")

            if isinstance(value, str) and value == "":
                LOG.warning(f"value for ref '{ref}' is empty")

            LOG.info(f"reference '{ref}' replaced by 'value'")

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
