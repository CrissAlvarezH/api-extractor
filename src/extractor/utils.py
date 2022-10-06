import logging
from typing import List

from src.common.repository import get_api_config, list_api_configs
from src.common.schemas import ApiConfig


LOG = logging.getLogger("utils")
LOG.setLevel(logging.INFO)


def get_configs(event) -> List[ApiConfig]:
    """ Return configs to execute 
    
    return config that coming on event on extractor_config_api key
    otherwise return all configs
    """
    config_id = event.get("extractor_config_id")
    if config_id:
        resp = get_api_config(config_id)
        if "Item" not in resp:
            LOG.error(f"config {config_id} does not exists")
            return
            
        configs = [resp["Item"]]
    else:
        # return all configs
        configs = list_api_configs()["Items"]

    LOG.info(f"Configs to execute {configs}")
    return [ApiConfig(**c) for c in configs]


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
    expression = expression.strip()

    if " " in expression:
        # then is <json_dot_syntax> <operator> <json_dot_syntax>
        dot_syntax_left, operator, dot_syntax_right = expression.split(" ")

        value_left = extract_from_json(data, dot_syntax_left)
        value_right = extract_from_json(data, dot_syntax_right)

        operator_executor = {
            "==": lambda x, y: x == y,
            ">": lambda x, y: x > y,
            ">=": lambda x, y: x >= y,
            "<": lambda x, y: x < y,
            "<=": lambda x, y: x <= y,
            "!=": lambda x, y: x != y,
        }

        result = operator_executor.get(operator)(value_left, value_right)
    else:
        # then is just <json_dot_syntax>
        result = extract_from_json(data, expression)

    LOG.info(f"result '{result}' from expression '{expression}' in data {data}")
    return result