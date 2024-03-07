/**
 * Copyright 2024 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

module "async-function" {
  source      = "github.com/GoogleCloudPlatform/cloud-foundation-fabric/modules/cloud-function-v2"
  project_id  = var.project
  region      = var.region
  name        = "orch-framework-async-function"
  bucket_name = "${var.project}-async-function-bucket"
  bucket_config = {
    force_destroy = true
  }
  bundle_config = {
    source_dir  = "../functions/orchestration-helpers/async-function"
    output_path = "bundle-orch-framework-async-function.zip"
  }
  function_config = {
    runtime = "python39"
  }
  environment_variables = {
    SIMPLE_DATAFORM_QUERY_EXECUTOR_URL = module.simple-dataform-query-executor.uri
    DATAFORM_LOCATION = var.dataform_location
    DATAFORM_PROJECT = var.dataform_project
    DATAFORM_REPO_NAME = var.dataform_repository
    WORKFLOW_CONTROL_PROJECT_ID = var.project
    WORKFLOW_CONTROL_DATASET_ID = module.bigquery-dataset.dataset_id
    WORKFLOW_CONTROL_TABLE_ID = "workflows_control"
  }
}

module "simple-dataform-query-executor" {
  source      = "github.com/GoogleCloudPlatform/cloud-foundation-fabric/modules/cloud-function-v2"
  project_id  = var.project
  region      = var.region
  name        = "orch-framework-simple-dataform-query-executor"
  bucket_name = "${var.project}-simple-dataform-query-executor-bucket"
  bucket_config = {
    force_destroy = true
  }
  bundle_config = {
    source_dir  = "../functions/data-processing-engines/simple-dataform-query-executor"
    output_path = "bundle-orch-framework-simple-dataform-query-executor.zip"
  }
  function_config = {
    runtime = "python39"
  }
}

module "bigquery-dataset" {
  source     = "github.com/GoogleCloudPlatform/cloud-foundation-fabric/modules/bigquery-dataset"
  project_id = var.project
  id         = "aef_orch_framework"
  tables = {
    workflows_control = {
      friendly_name       = "workflows_control"
      schema              = local.workflows_control
      deletion_protection = false
    }
  }
}

