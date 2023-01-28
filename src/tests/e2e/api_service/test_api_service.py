import os
import json
import time

import boto3 as boto
import pandas as pd
import requests


def test_config_base(api_base_url, fake_api_domain, config_api_key, fake_api_secret):
    # NOTE: before this run a fake api with ngrok to expose to internet

    data_file_path = os.path.join(os.path.dirname(__file__), "config_data.json")
    with open(data_file_path) as f:
        config = json.loads(f.read())["config_base"]

    # set env var to domain of ngrok
    config["auth"]["refresh_token"]["endpoint"]["url"] = config["auth"]["refresh_token"]["endpoint"]["url"] \
        .format(domain=fake_api_domain)
    for extraction in config["extractions"]:
        extraction["endpoint"]["url"] = extraction["endpoint"]["url"].format(domain=fake_api_domain)

    # insert config_base user POST request to api
    auth_header = {"Authorization": config_api_key}
    response = requests.post(f"{api_base_url}/config", headers=auth_header, json=config)
    assert response.status_code == 200, response.text

    config = response.json()

    # get secret values, update json to add 'base_secret' from environ variables and update secret
    api_extractor_secret_name = "api-extractor-config/prod/extractor-secrets"
    secretsmanager = boto.client("secretsmanager", region_name="us-east-2")
    secret_response = secretsmanager.get_secret_value(SecretId=api_extractor_secret_name)
    secret_value = json.loads(secret_response.get("SecretString"))
    secret_value.update({"base_secret": fake_api_secret})
    secretsmanager.update_secret(
        SecretId=api_extractor_secret_name,
        SecretString=json.dumps(secret_value)
    )

    # run the extractions on api config
    response = requests.post(f"{api_base_url}/config/{config['id']}/execute", headers=auth_header)
    assert response.status_code == 200, response.text

    # wait with a loop with 5 seconds of delay for the logs on the api endpoint for those extractions
    for extraction in config["extractions"]:
        max_attempts = 10
        attempts = 0
        completed = False
        while not completed and attempts <= max_attempts:
            time.sleep(2)
            attempts += 1

            response = requests.get(f"{api_base_url}/extractions/{extraction['id']}/logs", headers=auth_header)
            assert response.status_code == 200, f"get extraction logs for {extraction['id']}"

            items = response.json().get("Items")
            if len(items) > 0:
                completed = True

                extraction_log = items[0]
                assert extraction_log.get("success") == "true", extraction_log.get("error")

                s3_destiny = extraction_log["destiny"]
                filename = s3_destiny.split("/")[-1]
                file_key = extraction["s3_destiny"]["folder"] + filename

                s3 = boto.client("s3", region_name="us-east-2")
                s3_obj = s3.get_object(Bucket=extraction["s3_destiny"]["bucket"], Key=file_key)

                result_df = pd.read_csv(s3_obj["Body"], sep=extraction.get("output_params").get("csv_separator"))
                expected_csv_path = os.path.join(
                    os.path.dirname(__file__), "expected_data", f"{extraction['name']}.csv")
                expected_df = pd.read_csv(expected_csv_path, sep=";")

                assert result_df.shape == expected_df.shape

                # compare result with expected dataframe
                compare_columns = [
                    "person_id", "person_name", "person_email",
                    "description", "currency", "amount",
                    "transformed__description", "sub_description"
                ]
                for i in range(expected_df.shape[0]):
                    for column in compare_columns:
                        compare = result_df.loc[i][column] == expected_df.loc[i][column]
                        assert compare, f"Data unexpected on i:{i}, column '{column}'"

        assert completed, "Extraction logs was not founds"

    # delete config before created
    response = requests.delete(f"{api_base_url}/config/{config['id']}", headers=auth_header)
    assert response.status_code == 200, "Delete config"
