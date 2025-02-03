import logging
from datetime import datetime
import pandas as pd
from azure.storage.filedatalake import DataLakeServiceClient
import psycopg2
from psycopg2.extras import execute_values
import json
from config import METADATA_TABLE
import numpy as np



# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ETL_Process')

class AzureStorageClient:
    def __init__(self, storage_account_name, sas_token):
        self.account_name = storage_account_name
        self.sas_token = sas_token
        self.service_client = self._get_service_client()

    def _get_service_client(self):
        try:
            service_client = DataLakeServiceClient(
                account_url=f"https://{self.account_name}.dfs.core.windows.net",
                credential=self.sas_token
            )
            return service_client
        except Exception as e:
            logger.error(f"Error connecting to Azure Storage: {str(e)}")
            raise

    def list_files(self, container_name, folder_path):
        try:
            file_system_client = self.service_client.get_file_system_client(container_name)
            paths = file_system_client.get_paths(path=folder_path)
            return [(path.name, path.last_modified) for path in paths 
                    if not getattr(path, 'is_directory', False)]
        except Exception as e:
            logger.error(f"Error listing files from {folder_path}: {str(e)}")
            raise

    def read_file(self, container_name, file_path):
        try:
            file_system_client = self.service_client.get_file_system_client(container_name)
            file_client = file_system_client.get_file_client(file_path)
            
            download = file_client.download_file()
            data = download.readall()
            
            if file_path.endswith('.csv'):
                return pd.read_csv(pd.io.common.BytesIO(data))
            elif file_path.endswith('.json'):
                return pd.DataFrame(json.loads(data))
            else:
                raise ValueError(f"Unsupported file format: {file_path}")
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            raise

class PostgresClient:
    def __init__(self, host, database, user, password, port):
        self.connection_params = {
            'host': host,
            'database': database,
            'user': user,
            'password': password,
            'port': port
        }

    def get_connection(self):
        """Get a new database connection"""
        return psycopg2.connect(**self.connection_params)

    def _convert_numpy_types(self, data):
        """Convert numpy types to Python native types"""
        if isinstance(data, (list, tuple)):
            return [self._convert_numpy_types(item) for item in data]
        elif isinstance(data, np.integer):
            return int(data)
        elif isinstance(data, np.floating):
            return float(data)
        elif isinstance(data, np.datetime64):
            return pd.Timestamp(data).to_pydatetime()
        return data

    def execute_query(self, query, params=None):
        """Execute a single query"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    conn.commit()
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise

    def execute_many(self, query, data):
        """Execute many with type conversion"""
        try:
            converted_data = [tuple(self._convert_numpy_types(row)) for row in data]
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    execute_values(cur, query, converted_data)
                    conn.commit()
        except Exception as e:
            logger.error(f"Error executing batch query: {str(e)}")
            raise

    def read_sql_query(self, query, params=None):
        """Execute a query and return results as a DataFrame"""
        try:
            with self.get_connection() as conn:
                return pd.read_sql_query(query, conn, params=params)
        except Exception as e:
            logger.error(f"Error executing read query: {str(e)}")
            raise

    def get_last_processed_timestamp(self, folder):
        """Get last processed timestamp"""
        try:
            query = """
                SELECT last_processed_timestamp 
                FROM datamart.etl_metadata 
                WHERE folder_name = %s
            """
            df = self.read_sql_query(query, params=(folder,))
            return df['last_processed_timestamp'].iloc[0] if not df.empty else datetime.min
        except Exception as e:
            logger.error(f"Error getting last processed timestamp: {str(e)}")
            raise