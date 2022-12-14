import os

STAGE = os.getenv("STAGE")

CONFIG_TABLE_NAME = f"ApiExtractorConfig-{STAGE}"
CONFIG_HISTORY_TABLE_NAME = f"ApiExtractorConfigHistory-{STAGE}"

API_KEYS_SECRET_NAME = f"api-extractor-config/{STAGE}/apikeys"
EXTRACTOR_SECRETS_SECRET_NAME = f"api-extractor-config/{STAGE}/extractor-secrets"

API_EXTRACTOR_FUNCTION_NAME = f"api-extractor-{STAGE}-ApiExtractor"

EXTRACTOR_EXECUTION_LOGS_TABLE_NAME = f"ApiExtractorExecutionLogs-{STAGE}"

DESTINY_BUCKET_NAME = f"api-extractor-output-{STAGE}-{os.getenv('DEFAULT_OUTPUT_BUCKET_SUFFIX')}"
