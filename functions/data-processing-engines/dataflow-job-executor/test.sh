#!/bin/bash

# Project and environment variables
project=pso-amex-data-platform
location=us-central1
bucket=$project-test-bucket
job_name=J01_etl_step_1

wget "http://jdbc.postgresql.org/download/postgresql-42.6.1.jar"
gcloud storage buckets create gs://$bucket --location=$location
gsutil cp postgresql-42.6.1.jar gs://$bucket/postgresql-42.6.1.jar

# Create a new Dataflow template workspace
curl -X POST \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     -H "Content-Type: application/json" \
     -d '{
           "launchParameter": {
             "jobName": "'$job_name'",
             "parameters": {
               "driverJars": "'gs://$bucket/postgresql-42.6.1.jar'",
               "driverClassName": "org.postgresql.Driver",
               "connectionURL": "jdbc:postgresql://10.60.0.33:5432/postgres?user=user1&password=changeme",
               "outputTable": "pso-amex-data-platform.landing_sample_dataset.dataflow_postgres_table",
               "bigQueryLoadingTemporaryDirectory": "'gs://$bucket/tmp/'",
             },
             "containerSpecGcsPath": "gs://dataflow-templates-"'$location'"/latest/flex/Jdbc_to_BigQuery_Flex",
             "environment": { "maxWorkers": "10" }
          }
        }' \
     https://dataflow.googleapis.com/v1b3/projects/$project/locations/$location/flexTemplates:launch


