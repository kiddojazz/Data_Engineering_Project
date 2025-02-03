# Import Libraries
from datetime import datetime
from typing import List, Dict
from faker import Faker
import pandas as pd
import os
import uuid

#Generate Task Logs
def generate_task_logs(num_records: int, batch_size: int = 100000) -> List[Dict]:
    """Generate fake task log records using Faker"""
    fake = Faker()
    records = []
    
    priority_levels = ['High', 'Medium', 'Low']
    status_options = ['Completed', 'Failed', 'In Progress']
    
    for _ in range(num_records):
        # Generate random timestamps with end_time always after start_time
        start_time = fake.date_time_this_year().timestamp() * 1000  # Convert to milliseconds
        end_time = start_time + (fake.random_int(min=1800, max=28800) * 1000)  # Add 30 mins to 8 hours
        
        record = {
            'task_id': str(uuid.uuid4()),
            'project_name': fake.word(),
            'employee_id': fake.random_int(min=1000, max=9999),
            'task_type': fake.random_element(['Development', 'Testing', 'Design', 'Documentation']),
            'priority': fake.random_element(priority_levels),
            'status': fake.random_element(status_options),
            'hours_logged': fake.random_int(min=1, max=8),
            'start_time': start_time,
            'end_time': end_time
        }
        records.append(record)
        
        if len(records) >= batch_size:
            yield records
            records = []
    
    if records:
        yield records


# Save Files as Parquet
def save_to_parquet(df: pd.DataFrame, output_dir: str, batch_num: int):
    """Save DataFrame as parquet file"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        file_name = f"task_logs_{timestamp}_batch_{batch_num:04d}.parquet"
        file_path = os.path.join(output_dir, file_name)
        
        # Save as parquet
        df.to_parquet(file_path, index=False)
        
        print(f"Successfully saved batch {batch_num:04d} to {file_path}")
        
    except Exception as e:
        print(f"Error saving parquet file: {str(e)}")
        raise


#Run Main Function
def main():
    # Configuration
    total_records = 20_000_000  # 20 million records
    batch_size = 100_000  # 100k records per batch
    output_directory = "/lakehouse/default/Files/data_log/"
    
    try:
        processed_records = 0
        for batch_num, batch_records in enumerate(generate_task_logs(total_records, batch_size)):
            # Convert batch to DataFrame
            pandas_df = pd.DataFrame(batch_records)
            
            # Save to parquet
            save_to_parquet(pandas_df, output_directory, batch_num)
            
            processed_records += len(batch_records)
            completion_percentage = (processed_records / total_records) * 100
            
            print(f"Progress: {completion_percentage:.2f}% ({processed_records:,} / {total_records:,} records)")
            
    except Exception as e:
        print(f"Error processing data: {str(e)}")
        raise

if __name__ == "__main__":
    main()