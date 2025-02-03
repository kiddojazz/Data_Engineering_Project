-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS spark;

-- Project Metrics Table
CREATE TABLE IF NOT EXISTS spark.project_metrics (
    project_name VARCHAR(100) NOT NULL,
    total_tasks INTEGER NOT NULL,
    completed_tasks INTEGER NOT NULL,
    avg_duration DECIMAL(10,2),
    total_hours_logged DECIMAL(12,2),
    avg_hours_per_task DECIMAL(10,2),
    completion_rate DECIMAL(5,2),
    PRIMARY KEY (project_name)
);

-- Employee Metrics Table
CREATE TABLE IF NOT EXISTS spark.employee_metrics (
    employee_id INTEGER NOT NULL,
    tasks_assigned INTEGER NOT NULL,
    tasks_completed INTEGER NOT NULL,
    total_hours_logged DECIMAL(12,2),
    avg_task_duration DECIMAL(10,2),
    completion_rate DECIMAL(5,2),
    productivity_score DECIMAL(10,2),
    PRIMARY KEY (employee_id)
);

-- Time Analysis Table
CREATE TABLE IF NOT EXISTS spark.time_analysis (
    day_of_week INTEGER NOT NULL,  -- 1 (Sunday) to 7 (Saturday)
    start_hour INTEGER NOT NULL,   -- 0 to 23
    task_count INTEGER NOT NULL,
    avg_duration DECIMAL(10,2),
    total_hours DECIMAL(12,2),
    PRIMARY KEY (day_of_week, start_hour)
);

-- Priority Metrics Table
CREATE TABLE IF NOT EXISTS spark.priority_metrics (
    priority VARCHAR(20) NOT NULL,
    task_count INTEGER NOT NULL,
    avg_duration DECIMAL(10,2),
    total_hours DECIMAL(12,2),
    completion_rate DECIMAL(5,2),
    PRIMARY KEY (priority)
);

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_project_completion_rate 
ON spark.project_metrics(completion_rate);

CREATE INDEX IF NOT EXISTS idx_employee_productivity 
ON spark.employee_metrics(productivity_score);

CREATE INDEX IF NOT EXISTS idx_time_analysis_task_count 
ON spark.time_analysis(task_count);

CREATE INDEX IF NOT EXISTS idx_priority_completion_rate 
ON spark.priority_metrics(completion_rate);

-- Add table comments
COMMENT ON TABLE spark.project_metrics IS 'Project-level performance metrics and statistics';
COMMENT ON TABLE spark.employee_metrics IS 'Employee-level performance and productivity metrics';
COMMENT ON TABLE spark.time_analysis IS 'Time-based task distribution and performance analysis';
COMMENT ON TABLE spark.priority_metrics IS 'Task metrics categorized by priority level';


select * from spark.time_analysis
select * from spark.project_metrics
select * from spark.employee_metrics
select * from spark.time_analysis




