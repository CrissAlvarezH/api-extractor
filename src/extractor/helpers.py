import re
import logging
import json
from typing import Tuple, Union, Optional

from requests import JSONDecodeError

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

    @classmethod
    def _destructure_reference(cls, ref: str) -> Tuple[str, str, str]:
        """ remove ${ and } from ref ex: ${self::auth, def} -> self::auth.token, def """
        inside = ref[2:-1]  

        # get expression and default value
        if "," in inside:
            expression, default = inside.split(",")
            default = default.strip()
        else:
            expression = inside
            default = None

        # expression is like: self::name.second or last::age
        retrieve_from, ref_value = expression.strip().split("::")

        return retrieve_from, ref_value, default

    @classmethod
    def _retrieve_reference_value(
        cls, text: str, context: Optional[dict] = None
    ) -> str:
        # Extract reference params with syntax ${from::value, default}
        pattern = re.compile("(\${+[A-Za-z0-9 ,.;:\/_-]+})")
        refs = pattern.findall(text)

        for ref in refs:
            retrieve_from, ref_value, default = cls._destructure_reference(ref)

            # retrieve_from is searched in context
            # if there isn't in the context, just do nothing with this reference
            if context.get(retrieve_from) is not None:
                value = extract_from_json(context[retrieve_from], ref_value)
            else:
                continue
            
            if value is None:
                value = default

            if value is None:
                raise ValueError(f"Ref {ref} return null and don't have default value")

            # logging
            if isinstance(value, str) and value == "":
                LOG.warning(f"value for ref '{ref}' is empty")
            else:
                if retrieve_from == "secret":
                    value_to_log = f"***{value[-3:]}" if len(value) > 5 else "****"
                else:
                    value_to_log = value
                LOG.info(f"reference '{ref}' replaced by '{value_to_log}'")

            # replace ref by retrieved value
            text = text.replace(ref, value)

        return text

    @classmethod
    def replace(cls, json: dict, context: Optional[dict] = None) -> dict:
        """ replace all ${} references by its value in json """
        for key, value in json.items():
            if isinstance(value, dict):
                cls.replace(value, context)
            elif isinstance(value, str):
                json[key] = cls._retrieve_reference_value(json[key], context)
        return json
