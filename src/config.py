"""
src/config.py
Environment configuration manager.
Loads database and AWS S3 settings from .env using python-dotenv.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass(frozen=True)
class DatabaseConfig:
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    name: str = os.getenv("DB_NAME", "data_engineer_db")
    user: str = os.getenv("DB_USER", "postgres")
    password: str = os.getenv("DB_PASSWORD", "")

@dataclass(frozen=True)
class AWSConfig:
    region: str = os.getenv("AWS_REGION", "us-east-1")
    access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    s3_bucket: str = os.getenv("S3_BUCKET_NAME", "associate-data-engineer-pipeline-bucket")
    
    @property
    def has_credentials(self) -> bool:
        return bool(self.access_key_id and self.secret_access_key and self.s3_bucket)

@dataclass(frozen=True)
class PipelineConfig:
    raw_data_path: str = os.getenv("RAW_DATA_PATH", "data/raw/raw_sales_data.csv")
    processed_data_path: str = os.getenv("PROCESSED_DATA_PATH", "data/processed/clean_sales_data.csv")
    rejected_data_path: str = os.getenv("REJECTED_DATA_PATH", "data/rejected/rejected_records.csv")

db_config = DatabaseConfig()
aws_config = AWSConfig()
pipeline_config = PipelineConfig()