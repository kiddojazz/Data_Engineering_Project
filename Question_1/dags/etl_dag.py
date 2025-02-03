from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow.models import Variable
from etl_process import ETLProcess
from config import CONTAINER_NAME, CLICKUP_FOLDER, FLOAT_FOLDER  # Import config variables directly
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ETL_Airflow_DAG')

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

def run_clickup_etl(**context):
    """Execute ClickUp ETL process"""
    try:
        etl = ETLProcess()
        clickup_files = etl.storage_client.list_files(
            CONTAINER_NAME,  # Use imported config variable
            CLICKUP_FOLDER  # Use imported config variable
        )
        last_processed = etl.db_client.get_last_processed_timestamp(
            CLICKUP_FOLDER
        )
        
        for file_path, modified_date in clickup_files:
            if modified_date > last_processed:
                df = etl.storage_client.read_file(
                    CONTAINER_NAME,
                    file_path
                )
                transformed_df = etl.transform_clickup_data(df)
                etl.load_fact_table(transformed_df, 'fact_time_tracking')
                etl.update_metadata(CLICKUP_FOLDER, modified_date)
        
        logger.info("ClickUp ETL process completed successfully")
    except Exception as e:
        logger.error(f"ClickUp ETL process failed: {str(e)}")
        raise

def run_float_etl(**context):
    """Execute Float ETL process"""
    try:
        etl = ETLProcess()
        float_files = etl.storage_client.list_files(
            CONTAINER_NAME,  # Use imported config variable
            FLOAT_FOLDER  # Use imported config variable
        )
        last_processed = etl.db_client.get_last_processed_timestamp(
            FLOAT_FOLDER
        )
        
        for file_path, modified_date in float_files:
            if modified_date > last_processed:
                df = etl.storage_client.read_file(
                    CONTAINER_NAME,
                    file_path
                )
                transformed_df = etl.transform_float_data(df)
                etl.load_fact_table(transformed_df, 'fact_allocation')
                etl.update_metadata(FLOAT_FOLDER, modified_date)
        
        logger.info("Float ETL process completed successfully")
    except Exception as e:
        logger.error(f"Float ETL process failed: {str(e)}")
        raise

# Create the DAG
with DAG(
    'sora_etl_pipeline',
    default_args=default_args,
    description='ETL pipeline for ClickUp and Float data',
    schedule_interval='0 6 * * *',  # 7 AM WAT (6 AM UTC)
    start_date=days_ago(1),
    catchup=False,
    tags=['etl', 'sora'],
) as dag:

    # Task for ClickUp ETL
    process_clickup = PythonOperator(
        task_id='process_clickup_data',
        python_callable=run_clickup_etl,
        provide_context=True,
    )

    # Task for Float ETL
    process_float = PythonOperator(
        task_id='process_float_data',
        python_callable=run_float_etl,
        provide_context=True,
    )

    # Set task dependencies
    process_clickup >> process_float