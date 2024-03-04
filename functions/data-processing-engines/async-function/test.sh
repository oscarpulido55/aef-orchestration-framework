curl -m 70 -X POST https://us-central1-dp-111-orc.cloudfunctions.net/async-function -H "Authorization: bearer $(gcloud auth print-identity-token)" -H "Content-Type: application/json" -d '{
    "call_type": "get_id",
    "job_name": "J01_etl_step_1",
    "workflow_name": "workflow1",
    "execution_id" : "executionId1"
}
'

curl -m 70 -X POST https://us-central1-dp-111-orc.cloudfunctions.net/async-function -H "Authorization: bearer $(gcloud auth print-identity-token)" -H "Content-Type: application/json" -d '{
    "call_type": "get_status",
    "job_name": "J01_etl_step_1",
    "workflow_name": "workflow1",
    "execution_id" : "executionId1",
    "async_job_id" : "aef_definitions_workflow1_etl_step_1_sqlx_3a72f7ae-6744-40e7-ace3-4096ba7cf4bc"
}
'
