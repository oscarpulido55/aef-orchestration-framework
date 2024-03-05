create table dp-111-orc.dp_111_orc_workflows.workflows_control
(
    workflow_execution_id STRING,
    workflow_name STRING,
    job_name STRING,
    job_status STRING,
    start_date DATETIME,
    end_date DATETIME,
    error_code STRING,
    job_params STRING,
    log_path STRING,
    retry_count INTEGER,
    execution_time_seconds INTEGER,
    message STRING
)