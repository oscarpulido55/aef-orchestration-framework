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

project='dp-111-trf'
location='us-central1'
workflow_name='workflow1'
start_date="2019-01-01"
end_date="2019-01-01"
validation_date_pattern="%Y-%m-%d"
same_day_execution="YESTERDAY"
workflow_status="ENABLED"
workflow_properties='{"dataform_location":"europe-west2","dataform_project_id":"dp-111-trf","repository_name":"TestRepoDataform"}'

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