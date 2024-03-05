# Project and environment variables
project=pso-amex-data-platform
location=us-central1
repository_id=test-repo5

# SQL query and owner information
commitname=bqfile
filename=querytest.sql
query='SELECT * FROM `bigquery-public-data.austin_crime.crime` where clearance_date>${dataform.projectConfig.vars.start_date} LIMIT 1000'
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
            "'$filename'": {
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
     https://dataform.googleapis.com/v1beta1/projects/$project/locations/$location/repositories/$repository_id:readFile?path=$filename

# -----------------------------------------------------
# Execute the SQL query via Cloud Function
# -----------------------------------------------------
curl -m 70 -X POST https://us-central1-pso-amex-data-platform.cloudfunctions.net/simple-dataform-query-executor \
-H "Authorization: bearer $(gcloud auth print-identity-token)" \
-H "Content-Type: application/json" \
-d '{
  "location": "'$location'",
  "dataform_project_id": "'$project'",
  "bq_project_id": "'$project'",
  "repository_name": "'$repository_id'",
  "file_path":  "'$filename'",
  "query_variables":{
      "${dataform.projectConfig.vars.start_date}":"2019-01-01"
  }
}'

# Delete the Dataform workspace
curl -X DELETE \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     https://dataform.googleapis.com/v1beta1/projects/$project/locations/$location/repositories/$repository_id