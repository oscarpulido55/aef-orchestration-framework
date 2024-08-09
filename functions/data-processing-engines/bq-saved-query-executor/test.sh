#!/bin/bash
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


delete_dataform_repo=true
if [ $# -gt 0 ]; then
    delete_dataform_repo=$1
fi

# Project and environment variables
project=<PROJECT_ID>
location=us-central1
repository_id=test-repo5

# Dataform repository, test query, and JOB information
dataform_location=us-central1
dataform_project_id=<PROJECT_ID>
commitname=bqfile

definitions_dir=definitions
workflow_name=workflow1
job_name=J01_etl_step_1

filepath="${definitions_dir}/${workflow_name}/${job_name}.sqlx"

query='SELECT * FROM `bigquery-public-data.austin_crime.crime` where clearance_date>${dataform.projectConfig.vars.start_date} LIMIT 1000'
start_date="2019-01-01"
queryowner=youremail@google.com
query=$(echo "$query" | tr -d '\n')
encoded_query=$(echo -n "$query" | base64)

# -----------------------------------------------------
# Dataform API Interactions
# -----------------------------------------------------

# Create a new Dataform workspace
curl -X POST \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     -H "Content-Type: application/json" \
     -d '{
            "displayName": "my bq",
            "labels": {
              "single-file-asset-type": "bigquery"
            },
            "setAuthenticatedUserAdmin": true
          }' \
     https://dataform.googleapis.com/v1beta1/projects/$project/locations/$location/repositories?repositoryId=$repository_id

# Commit a new SQL file to the Dataform workspace
curl -X POST \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     -H "Content-Type: application/json" \
     -d '{
          "commitMetadata": {
            "author": {
              "name": "foo bar",
              "emailAddress": "'$queryowner'"
            },
            "commitMessage": "update bq query"
          },
          "fileOperations": {
            "'$filepath'": {
              "writeFile": {
                "contents": "'$encoded_query'"
              }
            }
          }
        }' \
     https://dataform.googleapis.com/v1beta1/projects/$project/locations/$location/repositories/$repository_id:commit

# Retrieve information about the Dataform workspace
curl -X GET \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     https://dataform.googleapis.com/v1beta1/projects/$project/locations/$location/repositories/$repository_id

# Get the access control policies for the workspace
curl -X GET \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     https://dataform.googleapis.com/v1beta1/projects/$project/locations/$location/repositories/$repository_id:getIamPolicy

# Read the contents of the committed SQL file
curl -X GET \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     https://dataform.googleapis.com/v1beta1/projects/$project/locations/$location/repositories/$repository_id:readFile?path=$filepath


if [ "$delete_dataform_repo" = "true" ]; then
    # -----------------------------------------------------
    # Execute the SQL query via Cloud Function
    # -----------------------------------------------------
    curl -m 70 -X POST https://$location-$project.cloudfunctions.net/orch-framework-simple-dataform-query-executor \
    -H "Authorization: bearer $(gcloud auth print-identity-token)" \
    -H "Content-Type: application/json" \
    -d '{
      "workflow_properties":{
        "dataform_location": "'$dataform_location'",
        "dataform_project_id": "'$dataform_project_id'",
        "repository_name": "'$repository_id'",
      },
      "workflow_name":  "'$workflow_name'",
      "job_name":  "'$job_name'",
      "query_variables":{
          "${dataform.projectConfig.vars.start_date}":"'$start_date'"
      }
    }'

    curl -X DELETE \
         -H "Authorization: Bearer $(gcloud auth print-access-token)" \
         https://dataform.googleapis.com/v1beta1/projects/$project/locations/$location/repositories/$repository_id
fi
