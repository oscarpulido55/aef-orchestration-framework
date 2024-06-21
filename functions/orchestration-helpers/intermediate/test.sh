# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

sh ../../data-processing-engines/simple-dataform-query-executor/test.sh false

project=analytics-engg-framework-demo
location=us-central1

job_name=J01_etl_step_1
workflow_name=workflow1
execution_id=executionId1
start_date="2019-01-01"
end_date="2019-01-01"
dataform_project="dp-111-trf"
dataform_location="europe-west2"
dataform_repository="TestRepoDataform"

async_job_id=$(curl -m 70 -X POST https://$location-$project.cloudfunctions.net/orch-framework-intermediate \
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

curl -m 70 -X POST https://$location-$project.cloudfunctions.net/orch-framework-intermediate \
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