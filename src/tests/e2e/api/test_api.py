import os
import json

import requests


def test_create_list_retrieve_and_delete_config(
        api_base_url, fake_api_domain, config_api_key, fake_api_secret
):
    data_file_path = os.path.join(os.path.dirname(__file__), "config_data.json")
    with open(data_file_path) as f:
        config = json.loads(f.read())["config_base"]

    auth_header = {"Authorization": config_api_key}

    # CREATE
    response = requests.post(f"{api_base_url}/config", json=config, headers=auth_header)
    created_config = response.json()

    assert response.status_code == 200, response.text
    assert created_config.get("name") == config.get('name')
    assert created_config.get("id")

    # RETRIEVE
    response = requests.get(f"{api_base_url}/config/{created_config.get('id')}", headers=auth_header)

    assert response.status_code == 200
    assert response.json()["name"] == created_config["name"]
    assert response.json()["id"] == created_config["id"]
    assert response.json()["extractions"][0]["name"] == created_config["extractions"][0]["name"]
    assert response.json()["extractions"][0]["id"] == created_config["extractions"][0]["id"]

    # LIST
    response = requests.get(f"{api_base_url}/config", headers=auth_header)
    list_body = response.json()

    assert response.status_code == 200
    assert len(list_body.get("Items", [])) == 1
    assert list_body.get("Items")[0]["id"] == created_config["id"]

    # UPDATE
    new_name = "Zoho updated"
    created_config["name"] = new_name
    response = requests.put(f"{api_base_url}/config/{created_config.get('id')}", json=created_config, headers=auth_header)

    assert response.status_code == 200
    assert response.json()["name"] == new_name

    response = requests.get(f"{api_base_url}/config/{created_config.get('id')}", headers=auth_header)
    assert response.json()["name"] == new_name

    # DELETE
    response = requests.delete(f"{api_base_url}/config/{created_config.get('id')}", headers=auth_header)

    assert response.status_code == 200

    response = requests.get(f"{api_base_url}/config/{created_config.get('id')}", headers=auth_header)
    assert response.status_code == 404

    response = requests.get(f"{api_base_url}/config", headers=auth_header)
    list_body = response.json()

    assert len(list_body.get("Items", [])) == 0
