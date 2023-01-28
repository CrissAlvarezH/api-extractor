import os

from pytest import fixture


def retrieve_env_var(name: str):
    value = os.environ.get(name)
    assert value, f"Error to get env var {name}"
    return value


@fixture(scope="session")
def api_base_url():
    return retrieve_env_var("CONFIG_API_BASE_URL")


@fixture(scope="session")
def fake_api_domain():
    return retrieve_env_var("FAKE_API_DOMAIN")


@fixture(scope="session")
def config_api_key():
    return retrieve_env_var("CONFIG_API_KEY")


@fixture(scope="session")
def fake_api_secret():
    return retrieve_env_var("FAKE_API_SECRET_TO_GET_TOKEN")
