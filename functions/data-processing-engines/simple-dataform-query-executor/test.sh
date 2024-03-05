#!/bin/bash

delete_dataform_repo=true
if [ $# -gt 0 ]; then
    delete_dataform_repo=$1
fi

# Project and environment variables
project=pso-amex-data-platform
location=us-central1
repository_id=test-repo5

# SQL query and owner information
dataform_location=us-central1
dataform_project_id=pso-amex-data-platform
commitname=bqfile

definitions_dir=definitions
workflow_name=workflow1
job_name=J01_etl_step_1

filepath="${definitions_dir}/${workflow_name}/${job_name}.sqlx"

query='SELECT * FROM `bigquery-public-data.austin_crime.crime` where clearance_date>${dataform.projectConfig.vars.start_date} LIMIT 1000'
start_date="2019-01-01"
queryowner=oscarpulido@google.com
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
      "dataform_location": "'$dataform_location'",
      "dataform_project_id": "'$dataform_project_id'",
      "repository_name": "'$repository_id'",
      "file_path":  "'$filepath'",
      "query_variables":{
          "${dataform.projectConfig.vars.start_date}":"'$start_date'"
      }
    }'

    curl -X DELETE \
         -H "Authorization: Bearer $(gcloud auth print-access-token)" \
         https://dataform.googleapis.com/v1beta1/projects/$project/locations/$location/repositories/$repository_id
fi
