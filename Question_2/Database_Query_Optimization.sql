
WITH time_tracking AS (
    SELECT 
        e.employee_id,
        e.employee_name,
        r.role_id,
        r.role_name,
        d.full_date,
        SUM(ft.hours_logged) as total_tracked_hours
    FROM datamart.fact_time_tracking ft
    INNER JOIN datamart.dim_employee e ON ft.employee_id = e.employee_id
    INNER JOIN datamart.dim_date d ON ft.date_id = d.date_id
    INNER JOIN datamart.fact_allocation fa ON ft.employee_id = fa.employee_id
    INNER JOIN datamart.dim_role r ON fa.role_id = r.role_id
    WHERE d.full_date BETWEEN '2024-01-01' AND '2024-12-31' 
    GROUP BY 
        e.employee_id,
        e.employee_name,
        r.role_id,
        r.role_name,
        d.full_date
),
allocation_hours AS (
    SELECT 
        e.employee_id,
        r.role_id,
        SUM(fa.estimated_hours) as total_allocated_hours
    FROM datamart.fact_allocation fa
    INNER JOIN datamart.dim_employee e ON fa.employee_id = e.employee_id
    INNER JOIN datamart.dim_role r ON fa.role_id = r.role_id
    GROUP BY 
        e.employee_id,
        r.role_id
)
SELECT 
    tt.employee_name,
    tt.role_name,
    tt.full_date,
    tt.total_tracked_hours,
    ah.total_allocated_hours
FROM time_tracking tt
INNER JOIN allocation_hours ah 
    ON tt.employee_id = ah.employee_id 
    AND tt.role_id = ah.role_id
WHERE tt.total_tracked_hours > 100
ORDER BY ah.total_allocated_hours DESC;





-- Add indexes for frequently joined columns
CREATE INDEX idx_fact_time_tracking_employee_date 
ON datamart.fact_time_tracking(employee_id, date_id);

CREATE INDEX idx_fact_allocation_employee_role 
ON datamart.fact_allocation(employee_id, role_id);

-- Add index for sorting
CREATE INDEX idx_fact_allocation_hours 
ON datamart.fact_allocation(estimated_hours);





































