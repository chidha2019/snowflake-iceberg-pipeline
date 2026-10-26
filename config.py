import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Local Files Directory Path
    LOCAL_FILES_DIR = r"C:\Users\JOHAN-PC-RYZEN9\Downloads\massmutual_local_csv_files\local_csv_files"

    SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
    SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
    SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
    SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
    SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
    SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
    SNOWFLAKE_STORAGE_INTEGRATION = os.getenv("SNOWFLAKE_STORAGE_INTEGRATION")
    SNOWFLAKE_EXTERNAL_VOLUME = os.getenv("SNOWFLAKE_EXTERNAL_VOLUME")

    AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

    GRAFANA_LOKI_URL = os.getenv("GRAFANA_LOKI_URL")
    GRAFANA_LOKI_USER = os.getenv("GRAFANA_LOKI_USER")
    GRAFANA_LOKI_PASSWORD = os.getenv("GRAFANA_LOKI_PASSWORD")

    @classmethod
    def validate(cls):
        required = [
            "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD", "SNOWFLAKE_ACCOUNT", 
            "SNOWFLAKE_DATABASE", "SNOWFLAKE_STORAGE_INTEGRATION", 
            "SNOWFLAKE_EXTERNAL_VOLUME", "AWS_BUCKET_NAME"
        ]
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required environment variables in .env: {', '.join(missing)}")

Config.validate()