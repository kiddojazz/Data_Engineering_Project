# Import Libraries
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, sum as _sum, avg as _avg, count, 
    from_unixtime, hour, minute, dayofweek,
    when, round, desc
)
from pyspark.sql.window import Window
import pyspark.sql.functions as F

#LOad Data and View

# Stage 1: Load the data
print("\n=== Stage 1: Loading Data ===")
input_path = "Files/data_log/"
task_logs_df = spark.read.parquet(input_path)
print("Initial Schema:")
task_logs_df.printSchema()


print("\nSample Raw Data:")
display(task_logs_df)

task_logs_df.describe().show()

# Convert Date Columns to Timestamp
# Stage 2: Convert timestamps and add time-based columns
print("\n=== Stage 2: Time Transformations ===")
time_transformed_df = task_logs_df \
    .withColumn("start_datetime", 
                from_unixtime((col("start_time") / 1000)).cast("timestamp")) \
    .withColumn("end_datetime", 
                from_unixtime((col("end_time") / 1000)).cast("timestamp")) \
    .withColumn("day_of_week", dayofweek("start_datetime")) \
    .withColumn("start_hour", hour("start_datetime")) \
    .withColumn("duration_hours", 
                round((col("end_time") - col("start_time")) / (1000 * 3600), 2))

print("\nData with Time Transformations:")
display(time_transformed_df)

# Data Quality Check
# Stage 3: Basic data quality checks
print("\n=== Stage 3: Data Quality Metrics ===")
total_records = time_transformed_df.count()
null_counts = time_transformed_df.select(
    [count(when(col(c).isNull(), c)).alias(c) for c in time_transformed_df.columns]
)
print("\nNull Counts per Column:")
null_counts.show()

print("\nStatus Distribution:")
time_transformed_df.groupBy("status").count() \
    .withColumn("percentage", round(col("count") * 100 / total_records, 2)) \
    .show()



# Stage 4: Project-level Analytics
print("\n=== Stage 4: Project Analytics ===")
project_metrics = time_transformed_df \
    .groupBy("project_name") \
    .agg(
        count("task_id").alias("total_tasks"),
        _sum(when(col("status") == "Completed", 1).otherwise(0)).alias("completed_tasks"),
        round(_avg("duration_hours"), 2).alias("avg_duration"),
        round(_sum("hours_logged"), 2).alias("total_hours_logged"),
        round(_avg("hours_logged"), 2).alias("avg_hours_per_task")
    ) \
    .withColumn("completion_rate", 
                round(col("completed_tasks") * 100 / col("total_tasks"), 2))

print("\nProject-level Metrics:")
project_metrics.orderBy(desc("total_tasks")).show(10)


# Stage 5: Employee Performance Analytics
print("\n=== Stage 5: Employee Analytics ===")
employee_metrics = time_transformed_df \
    .groupBy("employee_id") \
    .agg(
        count("task_id").alias("tasks_assigned"),
        _sum(when(col("status") == "Completed", 1).otherwise(0)).alias("tasks_completed"),
        round(_sum("hours_logged"), 2).alias("total_hours_logged"),
        round(_avg("duration_hours"), 2).alias("avg_task_duration")
    ) \
    .withColumn("completion_rate", 
                round(col("tasks_completed") * 100 / col("tasks_assigned"), 2)) \
    .withColumn("productivity_score", 
                round(col("tasks_completed") / col("total_hours_logged"), 2))

print("\nTop Performers by Completion Rate:")
employee_metrics.orderBy(desc("completion_rate")).show(10)


# Stage 6: Time-based Analysis
print("\n=== Stage 6: Time-based Analysis ===")
time_analysis = time_transformed_df \
    .groupBy("day_of_week", "start_hour") \
    .agg(
        count("task_id").alias("task_count"),
        round(_avg("duration_hours"), 2).alias("avg_duration"),
        round(_sum("hours_logged"), 2).alias("total_hours")
    )

print("\nTask Distribution by Day and Hour:")
time_analysis.orderBy("day_of_week", "start_hour").show(10)


# Stage 7: Priority-based Analysis
print("\n=== Stage 7: Priority Analysis ===")
priority_metrics = time_transformed_df \
    .groupBy("priority") \
    .agg(
        count("task_id").alias("task_count"),
        round(_avg("duration_hours"), 2).alias("avg_duration"),
        round(_sum("hours_logged"), 2).alias("total_hours"),
        round(_avg(when(col("status") == "Completed", 1).otherwise(0)) * 100, 2).alias("completion_rate")
    )

print("\nMetrics by Priority Level:")
priority_metrics.show()


# Stage 8: Save transformed and analyzed data
print("\n=== Stage 8: Saving Results ===")
output_path = "Files/clean_data_log/"

# Save project metrics
project_metrics \
    .coalesce(1) \
    .write \
    .mode("overwrite") \
    .option("header", "true") \
    .csv(f"{output_path}project_metrics")


# Save employee metrics
employee_metrics \
    .coalesce(1) \
    .write \
    .mode("overwrite") \
    .option("header", "true") \
    .csv(f"{output_path}employee_metrics")


# Save time analysis
time_analysis \
    .coalesce(1) \
    .write \
    .mode("overwrite") \
    .option("header", "true") \
    .csv(f"{output_path}time_analysis")


# Save priority metrics
priority_metrics \
    .coalesce(1) \
    .write \
    .mode("overwrite") \
    .option("header", "true") \
    .csv(f"{output_path}priority_metrics")

print("\nTransformation and analysis complete. Results saved to:", output_path)