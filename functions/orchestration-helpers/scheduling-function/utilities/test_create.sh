# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

workflow_properties='{"dataform_location":"europe-west2","dataform_project_id":"dp-111-trf","repository_name":"TestRepoDataform","dataproc_serverless_project_id":"diegodu-test-project-1","dataproc_serverless_region":"us-central1","jar_file_location":"gs://test-image-dd-bucket/spark-demo-cobrix-app-0.0.1.jar","spark_history_server_cluster":"example-history-server","spark_app_main_class":"com.example.spark.demo.cobrix.SparkDemoCobrixApp","spark_app_config_bucket":"gs://test-image-dd-bucket","dataproc_serverless_runtime_version":"1.1.57","spark_app_properties":{"spark.executor.instances":"2","spark.executor.cores":"4"}}'

python3 firestore_crud.py --gcp_project dp-111-trf \
                          --workflow_name workflow1 \
                          --operation_type CREATE \
                          --crond_expression '0 7 * * *' \
                          --time_zone 'America/Los_Angeles' \
                          --date_format '%Y-%m-%d' \
                          --workflow_status ENABLED \
                          --workflow_properties $workflow_properties