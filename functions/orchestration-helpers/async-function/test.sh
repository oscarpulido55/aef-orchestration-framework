sh ../../data-processing-engines/simple-dataform-query-executor/test.sh false

project=pso-amex-data-platform
location=us-central1

job_name=J01_etl_step_1
workflow_name=workflow1
execution_id=executionId1
start_date="2019-01-01"
end_date="2019-01-01"

async_job_id=$(curl -m 70 -X POST https://$location-$project.cloudfunctions.net/orch-framework-async-function \
-H "Authorization: bearer $(gcloud auth print-identity-token)" \
-H "Content-Type: application/json" \
-d '{
    "call_type": "get_id",
    "job_name": "'$job_name'",
    "workflow_name": "'$workflow_name'",
    "execution_id" : "'$execution_id'",
    "start_date" : "'$start_date'",
    "end_date" : "'$end_date'"
}')

echo "Job ID: "
echo $async_job_id

curl -m 70 -X POST https://$location-$project.cloudfunctions.net/orch-framework-async-function \
-H "Authorization: bearer $(gcloud auth print-identity-token)" \
-H "Content-Type: application/json" \
-d '{
    "call_type": "get_status",
    "job_name": "'$job_name'",
    "workflow_name": "'$workflow_name'",
    "execution_id" : "'$execution_id'",
    "async_job_id" : "'$async_job_id'",
    "start_date" : "'$start_date'",
    "end_date" : "'$end_date'"
}'