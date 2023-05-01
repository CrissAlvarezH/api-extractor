import logging
from typing import List, Union
from src.common.aws import config_db_table

from src.common.schemas import ApiConfig


LOG = logging.getLogger("utils")
LOG.setLevel(logging.INFO)


def get_configs(event) -> Union[List[ApiConfig], None]:
    """ Return configs to execute 
    
    return config that coming on event on extractor_config_api key
    otherwise return all configs
    """
    config_id = event.get("extractor_config_id")
    table, _ = config_db_table()
    if config_id:
        resp = table.get_item(Key={"id": config_id})
        if "Item" not in resp:
            LOG.error(f"config {config_id} does not exists")
            return
            
        configs = [resp["Item"]]
    else:
        configs = table.scan()["Items"]

    configs = [ApiConfig(**c) for c in configs]
    LOG.info(f"Configs to execute {[str(c) for c in configs]}")
    return configs


def extract_from_json(data: dict, dot_syntax: str):
    """ Extract value from 'data' using 'dot_syntax' has json path 
    
    for instance:
    'dot_syntax' is like 'user.account.number'
    'data' is {"user": {"account": {"number": "23455"}}}
    and return value must be "23455"
    """
    temp = data
    for key in dot_syntax.split("."):
        if type(temp) is not dict:
            """ return None because this value is not a dict and the 
                dot_syntax is attempting to get a value if it were a dict"""
            return None

        if key not in temp:
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

    LOG.info(f"result '{result}' from expression '{expression}'")
    return result


def replace_decimal(obj: dict):
    for key, value in obj.items():
        if isinstance(value, dict):
            replace_decimal(value)
        elif isinstance(value, int) or isinstance(value, float):
            obj[key] = str(value)
    return obj
