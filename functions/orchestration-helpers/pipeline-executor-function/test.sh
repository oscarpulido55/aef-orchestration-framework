project='dp-111-trf'
location='us-central1'
workflow_name='workflow1'
start_date="2019-01-01"
end_date="2019-01-01"
validation_date_pattern="%Y-%m-%d"
same_day_execution="YESTERDAY"
workflow_status="ENABLED"
workflow_properties='{"database_project_id":"prj-111"}'

async_job_id=$(curl -m 70 -X POST https://$location-$project.cloudfunctions.net/orch-framework-pipeline-executor-function \
-H "Authorization: bearer $(gcloud auth print-identity-token)" \
-H "Content-Type: application/json" \
-d '{
    "workflows_name": "'$workflow_name'",
    "validation_date_pattern": "'$validation_date_pattern'",
    "same_day_execution": "'$same_day_execution'",
    "workflow_status": "'$workflow_status'",
    "workflow_properties": '$workflow_properties',
    "start_date" : "'$start_date'",
    "end_date" : "'$end_date'"
}')

echo "Workflow Execution ID: "
echo $async_job_id