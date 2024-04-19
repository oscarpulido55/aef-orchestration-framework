sh ../../data-processing-engines/simple-dataform-query-executor/test.sh false

project=pso-amex-data-platform
location=us-central1

job_name=J01_etl_step_1
workflow_name=workflow1
execution_id=executionId1
start_date="2019-01-01"
end_date="2019-01-01"
dataform_project="dp-111-trf"
dataform_location="europe-west2"
dataform_repository="TestRepoDataform"

async_job_id=$(curl -m 70 -X POST https://$location-$project.cloudfunctions.net/orch-framework-intermediate-function \
-H "Authorization: bearer $(gcloud auth print-identity-token)" \
-H "Content-Type: application/json" \
-d '{
    "call_type": "get_id",
    "job_name": "'$job_name'",
    "workflow_name": "'$workflow_name'",
    "execution_id" : "'$execution_id'",
    "query_variables":{
        "start_date" : "'$start_date'",
        "end_date" : "'$end_date'"
    },
    "workflow_properties": {
        "dataform_location": "'$dataform_location'",
        "dataform_project_id": "'$dataform_project'",
        "repository_name": "'$dataform_repository'"
    }
}')



echo "Job ID: "
echo $async_job_id

curl -m 70 -X POST https://$location-$project.cloudfunctions.net/orch-framework-intermediate-function \
-H "Authorization: bearer $(gcloud auth print-identity-token)" \
-H "Content-Type: application/json" \
-d '{
    "call_type": "get_status",
    "job_name": "'$job_name'",
    "workflow_name": "'$workflow_name'",
    "execution_id" : "'$execution_id'",
    "async_job_id" : "'$async_job_id'",
    "query_variables":{
        "start_date" : "'$start_date'",
        "end_date" : "'$end_date'"
    },
    "workflow_properties": {
        "dataform_location": "'$dataform_location'",
        "dataform_project_id": "'$dataform_project'",
        "repository_name": "'$dataform_repository'"
    }
}'