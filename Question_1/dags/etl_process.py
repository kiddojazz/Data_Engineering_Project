from config import *
from utils import AzureStorageClient, PostgresClient, logger
import pandas as pd
from datetime import datetime
import numpy as np

class ETLProcess:
    def __init__(self):
        self.storage_client = AzureStorageClient(STORAGE_ACCOUNT_NAME, SAS_TOKEN)
        self.db_client = PostgresClient(DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT)
    
    def ensure_date_dimension(self, dates):
        """
        Ensure all required dates exist in dim_date
        Returns a mapping of datetime to date_id
        """
        try:
            # Get unique dates and extend range to cover end dates
            all_dates = pd.to_datetime(sorted(set(dates)))
            if not all_dates.empty:
                date_range = pd.date_range(
                    start=all_dates.min(),
                    end=all_dates.max(),
                    freq='D'
                )
                
                # Get existing dates
                query = "SELECT date_id, full_date FROM datamart.dim_date"
                existing_dates = self.db_client.read_sql_query(query)
                existing_dates['full_date'] = pd.to_datetime(existing_dates['full_date'])
                
                # Find missing dates
                missing_dates = date_range[~date_range.isin(existing_dates['full_date'])]
                
                if len(missing_dates) > 0:
                    insert_query = """
                        INSERT INTO datamart.dim_date 
                        (date_id, full_date, year, month, day, quarter)
                        VALUES %s
                    """
                    data = [
                        (
                            int(d.strftime('%Y%m%d')),
                            d.date(),
                            int(d.year),
                            int(d.month),
                            int(d.day),
                            int((d.month - 1) // 3 + 1)
                        )
                        for d in missing_dates
                    ]
                    self.db_client.execute_many(insert_query, data)
                
                # Get complete date mapping
                date_mapping = self.db_client.read_sql_query(query)
                date_mapping['full_date'] = pd.to_datetime(date_mapping['full_date'])
                return date_mapping.set_index('full_date')['date_id'].to_dict()
                
        except Exception as e:
            logger.error(f"Error ensuring date dimension: {str(e)}")
            raise

    def process_dimension_table(self, df, dim_name, source_column, key_column, client_id=None):
        """
        Generic dimension table processing with optional client_id for projects
        """
        try:
            # Get existing dimension values
            if dim_name == 'project':
                query = f"SELECT {key_column}, {dim_name}_id, client_id FROM datamart.dim_{dim_name}"
            else:
                query = f"SELECT {key_column}, {dim_name}_id FROM datamart.dim_{dim_name}"
            
            existing_dim = pd.read_sql(query, self.db_client.get_connection())
            
            # Create a temporary df with renamed column to match dimension table
            temp_df = df[[source_column]].copy()
            temp_df.columns = [key_column]
            
            # Find new values
            new_values = temp_df[~temp_df[key_column].isin(existing_dim[key_column])]
            
            if not new_values.empty:
                if dim_name == 'project':
                    insert_query = f"""
                        INSERT INTO datamart.dim_{dim_name} 
                        ({key_column}, client_id, created_date, modified_date)
                        VALUES %s
                    """
                    data = [
                        (row[key_column], client_id, datetime.now(), datetime.now())
                        for _, row in new_values.iterrows()
                    ]
                else:
                    insert_query = f"""
                        INSERT INTO datamart.dim_{dim_name} 
                        ({key_column}, created_date, modified_date)
                        VALUES %s
                    """
                    data = [
                        (row[key_column], datetime.now(), datetime.now())
                        for _, row in new_values.iterrows()
                    ]
                self.db_client.execute_many(insert_query, data)
                
            # Get updated mapping including new values
            mapping = pd.read_sql(query, self.db_client.get_connection())
            return mapping
        except Exception as e:
            logger.error(f"Error processing dimension {dim_name}: {str(e)}")
            raise

    def transform_clickup_data(self, df):
        """Transform ClickUp data"""
        try:
            df['Date'] = pd.to_datetime(df['Date'])
            df['Billable'] = df['Billable'].map({'Yes': True, 'No': False})
            df['Hours'] = pd.to_numeric(df['Hours'], errors='coerce')
            
            # Ensure dates exist in dimension
            date_mapping = self.ensure_date_dimension(df['Date'])
            
            # Process dimensions in correct order (client first, then project)
            client_mapping = self.process_dimension_table(
                df, 'client', 'Client', 'client_name'
            )
            
            # For each project, we need to associate it with its client
            project_mapping = pd.DataFrame()
            for client_name in df['Client'].unique():
                client_id = client_mapping[
                    client_mapping['client_name'] == client_name
                ]['client_id'].iloc[0]
                
                client_projects = df[df['Client'] == client_name]
                project_map = self.process_dimension_table(
                    client_projects, 
                    'project', 
                    'Project', 
                    'project_name',
                    client_id=client_id
                )
                project_mapping = pd.concat([project_mapping, project_map])
            
            employee_mapping = self.process_dimension_table(
                df, 'employee', 'Name', 'employee_name'
            )
            
            # Transform data for fact table
            transformed_data = []
            for _, row in df.iterrows():
                transformed_data.append({
                    'employee_id': employee_mapping[
                        employee_mapping['employee_name'] == row['Name']
                    ]['employee_id'].iloc[0],
                    'project_id': project_mapping[
                        project_mapping['project_name'] == row['Project']
                    ]['project_id'].iloc[0],
                    'date_id': date_mapping[row['Date']],
                    'task_name': row['Task'],
                    'hours_logged': row['Hours'],
                    'billable': row['Billable'],
                    'notes': row['Note'],
                    'created_date': datetime.now(),
                    'modified_date': datetime.now()
                })
            
            return pd.DataFrame(transformed_data)
        except Exception as e:
            logger.error(f"Error transforming ClickUp data: {str(e)}")
            raise

    def transform_float_data(self, df):
        """Transform Float data"""
        try:
            df['Start Date'] = pd.to_datetime(df['Start Date'])
            df['End Date'] = pd.to_datetime(df['End Date'])
            df['Estimated Hours'] = pd.to_numeric(df['Estimated Hours'], errors='coerce')
            
            # Ensure all dates exist in dimension
            dates = pd.concat([df['Start Date'], df['End Date']])
            date_mapping = self.ensure_date_dimension(dates)
            
            # Process dimensions in correct order (client first, then project)
            client_mapping = self.process_dimension_table(
                df, 'client', 'Client', 'client_name'
            )
            
            # For each project, we need to associate it with its client
            project_mapping = pd.DataFrame()
            for client_name in df['Client'].unique():
                client_id = client_mapping[
                    client_mapping['client_name'] == client_name
                ]['client_id'].iloc[0]
                
                client_projects = df[df['Client'] == client_name]
                project_map = self.process_dimension_table(
                    client_projects, 
                    'project', 
                    'Project', 
                    'project_name',
                    client_id=client_id
                )
                project_mapping = pd.concat([project_mapping, project_map])
            
            employee_mapping = self.process_dimension_table(
                df, 'employee', 'Name', 'employee_name'
            )
            
            role_mapping = self.process_dimension_table(
                df, 'role', 'Role', 'role_name'
            )
            
            # Transform data for fact table
            transformed_data = []
            for _, row in df.iterrows():
                transformed_data.append({
                    'employee_id': employee_mapping[
                        employee_mapping['employee_name'] == row['Name']
                    ]['employee_id'].iloc[0],
                    'project_id': project_mapping[
                        project_mapping['project_name'] == row['Project']
                    ]['project_id'].iloc[0],
                    'role_id': role_mapping[
                        role_mapping['role_name'] == row['Role']
                    ]['role_id'].iloc[0],
                    'start_date_id': date_mapping[row['Start Date']],
                    'end_date_id': date_mapping[row['End Date']],
                    'estimated_hours': row['Estimated Hours'],
                    'created_date': datetime.now(),
                    'modified_date': datetime.now()
                })
            
            return pd.DataFrame(transformed_data)
        except Exception as e:
            logger.error(f"Error transforming Float data: {str(e)}")
            raise

    def load_fact_table(self, df, table_name):
        """Load data into fact table"""
        try:
            columns = ', '.join(df.columns)
            insert_query = f"""
                INSERT INTO datamart.{table_name} ({columns})
                VALUES %s
            """
            data = [tuple(row) for row in df.values]
            self.db_client.execute_many(insert_query, data)
        except Exception as e:
            logger.error(f"Error loading data into {table_name}: {str(e)}")
            raise

    def update_metadata(self, folder, timestamp):
        """Update metadata table with last processed timestamp"""
        query = """
            INSERT INTO datamart.etl_metadata (folder_name, last_processed_timestamp)
            VALUES (%s, %s)
            ON CONFLICT (folder_name) 
            DO UPDATE SET last_processed_timestamp = EXCLUDED.last_processed_timestamp
        """
        self.db_client.execute_query(query, (folder, timestamp))

    def run(self):
        """Main ETL process"""
        try:
            # Process ClickUp data
            clickup_files = self.storage_client.list_files(CONTAINER_NAME, CLICKUP_FOLDER)
            last_processed = self.db_client.get_last_processed_timestamp(CLICKUP_FOLDER)
            
            for file_path, modified_date in clickup_files:
                if modified_date > last_processed:
                    df = self.storage_client.read_file(CONTAINER_NAME, file_path)
                    transformed_df = self.transform_clickup_data(df)
                    self.load_fact_table(transformed_df, 'fact_time_tracking')
                    self.update_metadata(CLICKUP_FOLDER, modified_date)
            
            # Process Float data
            float_files = self.storage_client.list_files(CONTAINER_NAME, FLOAT_FOLDER)
            last_processed = self.db_client.get_last_processed_timestamp(FLOAT_FOLDER)
            
            for file_path, modified_date in float_files:
                if modified_date > last_processed:
                    df = self.storage_client.read_file(CONTAINER_NAME, file_path)
                    transformed_df = self.transform_float_data(df)
                    self.load_fact_table(transformed_df, 'fact_allocation')
                    self.update_metadata(FLOAT_FOLDER, modified_date)
            
            logger.info("ETL process completed successfully")
            
        except Exception as e:
            logger.error(f"ETL process failed: {str(e)}")
            raise

if __name__ == "__main__":
    etl = ETLProcess()
    etl.run()