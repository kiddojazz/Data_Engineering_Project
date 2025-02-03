-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS datamart;

-- Client Dimension
CREATE TABLE datamart.dim_client (
    client_id SERIAL PRIMARY KEY,
    client_name VARCHAR(100),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Project Dimension
CREATE TABLE datamart.dim_project (
    project_id SERIAL PRIMARY KEY,
    project_name VARCHAR(100),
    client_id INTEGER REFERENCES datamart.dim_client(client_id),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Employee Dimension
CREATE TABLE datamart.dim_employee (
    employee_id SERIAL PRIMARY KEY,
    employee_name VARCHAR(100),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Role Dimension
CREATE TABLE datamart.dim_role (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(100),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Date Dimension
CREATE TABLE datamart.dim_date (
    date_id INTEGER PRIMARY KEY,
    full_date DATE,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    quarter INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fact Time Tracking
CREATE TABLE datamart.fact_time_tracking (
    time_tracking_id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES datamart.dim_employee(employee_id),
    project_id INTEGER REFERENCES datamart.dim_project(project_id),
    date_id INTEGER REFERENCES datamart.dim_date(date_id),
    task_name VARCHAR(100),
    hours_logged DECIMAL(5,2),
    billable BOOLEAN,
    notes TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fact Allocation
CREATE TABLE datamart.fact_allocation (
    allocation_id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES datamart.dim_employee(employee_id),
    project_id INTEGER REFERENCES datamart.dim_project(project_id),
    role_id INTEGER REFERENCES datamart.dim_role(role_id),
    start_date_id INTEGER REFERENCES datamart.dim_date(date_id),
    end_date_id INTEGER REFERENCES datamart.dim_date(date_id),
    estimated_hours DECIMAL(5,2),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create ETL metadata table
CREATE TABLE datamart.etl_metadata (
    id SERIAL PRIMARY KEY,
    folder_name VARCHAR(100) NOT NULL UNIQUE,
    last_processed_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster lookups
CREATE INDEX idx_etl_metadata_folder ON datamart.etl_metadata(folder_name);

-- Create indexes for better query performance
CREATE INDEX idx_dim_project_client_id ON datamart.dim_project(client_id);
CREATE INDEX idx_fact_time_tracking_employee ON datamart.fact_time_tracking(employee_id);
CREATE INDEX idx_fact_time_tracking_project ON datamart.fact_time_tracking(project_id);
CREATE INDEX idx_fact_time_tracking_date ON datamart.fact_time_tracking(date_id);
CREATE INDEX idx_fact_allocation_employee ON datamart.fact_allocation(employee_id);
CREATE INDEX idx_fact_allocation_project ON datamart.fact_allocation(project_id);
CREATE INDEX idx_fact_allocation_role ON datamart.fact_allocation(role_id);
CREATE INDEX idx_fact_allocation_dates ON datamart.fact_allocation(start_date_id, end_date_id);

