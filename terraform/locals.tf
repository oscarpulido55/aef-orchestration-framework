locals {
  workflows_control = jsonencode([
    { name = "workflow_execution_id", type = "STRING" },
    { name = "workflow_name", type = "STRING" },
    { name = "job_name", type = "STRING" },
    { name = "job_status", type = "STRING" },
    { name = "start_date", type = "DATETIME" },
    { name = "end_date", type = "DATETIME" },
    { name = "error_code", type = "STRING" },
    { name = "job_params", type = "STRING" },
    { name = "log_path", type = "STRING" },
    { name = "retry_count", type = "INTEGER" },
    { name = "execution_time_seconds", type = "INTEGER" },
    { name = "message", type = "STRING" }
  ])
}