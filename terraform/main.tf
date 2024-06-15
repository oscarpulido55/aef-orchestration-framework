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

module "pipeline-executor-function" {
  source      = "github.com/GoogleCloudPlatform/cloud-foundation-fabric/modules/cloud-function-v2"
  project_id  = var.project
  region      = var.region
  name        = "orch-framework-pipeline-executor"
  bucket_name = "${var.project}-pipeline-executor-function-bucket"
  bucket_config = {
    force_destroy = true
  }
  bundle_config = {
    path  = "../functions/orchestration-helpers/pipeline-executor"
  }
  function_config = {
    runtime = "python39",
    instance_count = 200
  }
  environment_variables = {
    WORKFLOW_CONTROL_PROJECT_ID = var.project
    WORKFLOW_CONTROL_DATASET_ID = module.bigquery-dataset.dataset_id
    WORKFLOW_CONTROL_TABLE_ID = "workflows_control"
    WORKFLOWS_LOCATION = var.region
  }
}

module "intermediate-function" {
  source      = "github.com/GoogleCloudPlatform/cloud-foundation-fabric/modules/cloud-function-v2"
  project_id  = var.project
  region      = var.region
  name        = "orch-framework-intermediate"
  bucket_name = "${var.project}-intermediate-function-bucket"
  bucket_config = {
    force_destroy = true
  }
  bundle_config = {
    path  = "../functions/orchestration-helpers/intermediate"
  }
  function_config = {
    runtime = "python39",
    instance_count = 200
  }
  environment_variables = {
    WORKFLOW_CONTROL_PROJECT_ID = var.project
    WORKFLOW_CONTROL_DATASET_ID = module.bigquery-dataset.dataset_id
    WORKFLOW_CONTROL_TABLE_ID = "workflows_control"
  }
}

#project reference to get project number
data "google_project" "project" {
  project_id = var.project
}

module "scheduling-function" {
  source      = "github.com/GoogleCloudPlatform/cloud-foundation-fabric/modules/cloud-function-v2"
  project_id  = var.project
  region      = var.region
  name        = "orch-framework-scheduling"
  bucket_name = "${var.project}-scheduling-function-bucket"
  bucket_config = {
    force_destroy = true
  }
  bundle_config = {
    path  = "../functions/orchestration-helpers/scheduling"
  }
  function_config = {
    runtime = "python39",
    instance_count = 200
  }
  environment_variables = {
    WORKFLOW_SCHEDULING_FIRESTORE_COLLECTION = var.workflows_scheduling_table_name
    WORKFLOW_SCHEDULING_PROJECT_ID = var.project
    WORKFLOW_SCHEDULING_PROJECT_NUMBER = data.google_project.project.number
    WORKFLOW_SCHEDULING_PROJECT_REGION = var.region
    PIPELINE_EXECUTION_FUNCTION_NAME = module.pipeline-executor-function.function_name
  }
  trigger_config = {
    event_type = "google.cloud.firestore.document.v1.written"
    event_filters = [
      {
        attribute = "database"
        value="(default)"
      }
    ]
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

