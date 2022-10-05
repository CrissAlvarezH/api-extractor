import os

STAGE = os.getenv("STAGE")

CONFIG_TABLE_NAME = f"ApiExtractorConfig-{STAGE}"
CONFIG_HISTORY_TABLE_NAME = f"ApiExtractorConfigHistory-{STAGE}"

API_KEYS_SECRET_NAME = f"api-extractor-config/{STAGE}/apikeys"

API_EXTRACTOR_FUNCTION_NAME = f"api-extractor-{STAGE}-ApiExtractor"
