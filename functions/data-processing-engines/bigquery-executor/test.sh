project=pso-amex-data-platform
location=us-central1
repository_id=test-repo4
commitname=bqfile
query="SELECT row_number() OVER (ORDER BY total_bytes_billed) row_num, total_bytes_billed, total_slot_ms, statement_type, job_type, query FROM dataset1.testlargetable order by row_num LIMIT 1000"
encoded_query=$(echo -n "$query" | base64)

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


curl -X POST \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     -H "Content-Type: application/json" \
     -d '{
          "commitMetadata": {
            "author": {
              "name": "foo bar",
              "emailAddress": "oscarpulido@google.com"
            },
            "commitMessage": "update bq query"
          },
          "fileOperations": {
            "querytest.sql": {
              "writeFile": {
                "contents": "'$encoded_query'"
              }
            }
          }
        }' \
     https://dataform.googleapis.com/v1beta1/projects/$project/locations/$location/repositories/$repository_id:commit



curl -X GET \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     https://dataform.googleapis.com/v1beta1/projects/$project/locations/$location/repositories/$repository_id

curl -X GET \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     https://dataform.googleapis.com/v1beta1/projects/$project/locations/$location/repositories/$repository_id:getIamPolicy

curl -X GET \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     https://dataform.googleapis.com/v1beta1/projects/$project/locations/$location/repositories/$repository_id:readFile?path=querytest.sql


curl -m 70 -X POST https://us-central1-pso-amex-data-platform.cloudfunctions.net/cf_bigquery_executor \
-H "Authorization: bearer $(gcloud auth print-identity-token)" \
-H "Content-Type: application/json" \
-d '{
  "location": "us-central1",
  "project_id": "pso-amex-data-platform",
  "repository_name": "test-repo4",
  "file_path": "querytest.sql"
}'