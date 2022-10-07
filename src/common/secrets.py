import json
from typing import Union

from .constants import API_KEYS_SECRET_NAME
from .aws import api_keys_secrets


def get_api_key_name(key_value: str) -> Union[str, None]:
    _, api_keys = api_keys_secrets()

    found = [k[0] for k in api_keys.items() if k[1] == key_value]
    return found[0] if len(found) > 0 else None


def add_or_update_api_key(name: str, value: str):
    client, api_keys = api_keys_secrets()
    api_keys.update({name: value})
    client.update_secret(
        SecretId=API_KEYS_SECRET_NAME,
        SecretString=json.dumps(api_keys)
    )

    return value


def remove_api_key(name: str):
    client, api_keys = api_keys_secrets()

    del api_keys[name]

    client.update_secret(
        SecretId=API_KEYS_SECRET_NAME,
        SecretString=json.dumps(api_keys)
    )
