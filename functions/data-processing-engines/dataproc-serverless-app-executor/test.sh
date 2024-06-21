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


location='us-central1'
project='dp-111-trf'
dataproc_serverless_project_id='diegodu-test-project-1'
dataproc_serverless_region='us-central1'
workflow_name='workflow1'
job_name="J01_etl_step_1"
start_date="2019-01-01"
jar_file_location="gs://test-image-dd-bucket/spark-dv-test-app-0.0.1-SNAPSHOT.jar"
spark_history_server_cluster="example-history-server"
spark_app_main_class="com.example.spark.cobol.app.SparkDvTestApp"
spark_app_config_bucket="gs://test-image-dd-bucket"
dataproc_serverless_runtime_version="1.1.57"

async_job_id=$(curl -m 70 -X POST https://$location-$project.cloudfunctions.net/orch-framework-dataproc-serverless-app-executor \
-H "Authorization: bearer $(gcloud auth print-identity-token)" \
-H "Content-Type: application/json" \
-d '{
  "workflow_name":  "'$workflow_name'",
  "job_name":  "'$job_name'",
  "workflow_properties":{
          "dataproc_serverless_project_id": "'$dataproc_serverless_project_id'",
          "dataproc_serverless_region": "'$dataproc_serverless_region'",
          "jar_file_location": "'$jar_file_location'",
          "spark_history_server_cluster": "'$spark_history_server_cluster'",
          "spark_app_main_class": "'$spark_app_main_class'",
          "spark_app_config_bucket": "'$spark_app_config_bucket'",
          "dataproc_serverless_runtime_version": "'$dataproc_serverless_runtime_version'",
          "spark_app_properties": {"spark.executor.instances": "2","spark.executor.core": "2"}

  },
  "query_variables":{
      "${dataform.projectConfig.vars.start_date}":"'$start_date'"
  }
}')

echo "Job ID: "
echo $async_job_id

sleep 10

curl -m 70 -X POST https://$location-$project.cloudfunctions.net/orch-framework-dataproc-serverless-app-executor \
-H "Authorization: bearer $(gcloud auth print-identity-token)" \
-H "Content-Type: application/json" \
-d '{
  "workflow_name":  "'$workflow_name'",
  "job_name":  "'$job_name'",
  "job_id":  "'$async_job_id'",
  "workflow_properties":{
          "dataproc_serverless_project_id": "'$dataproc_serverless_project_id'",
          "dataproc_serverless_region": "'$dataproc_serverless_region'"
  }
}'