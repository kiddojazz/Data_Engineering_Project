from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Azure Storage configuration
STORAGE_ACCOUNT_NAME = os.getenv('STORAGE_ACCOUNT_NAME')
CONTAINER_NAME = os.getenv('CONTAINER_NAME', 'sora_container')
SAS_TOKEN = os.getenv('SAS_TOKEN')

# Azure PostgreSQL configuration
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT = os.getenv('DB_PORT', '5432')

# File paths
FLOAT_FOLDER = 'Float'
CLICKUP_FOLDER = 'Clickup'

# Metadata table name for tracking last processed files
METADATA_TABLE = 'datamart.etl_metadata'