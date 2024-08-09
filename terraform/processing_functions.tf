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

module "aef-processing-function-sa" {
  source     = "github.com/GoogleCloudPlatform/cloud-foundation-fabric/modules/iam-service-account"
  project_id = var.project
  name       = "aef-processing-function-sa"

  # non-authoritative roles granted *to* the service accounts on other resources
  iam_project_roles = {
    "${var.project}" = [
      "roles/editor",
      "roles/secretmanager.secretAccessor",
      "roles/dataproc.worker",
      "roles/compute.networkUser"
    ]
  }
}

module "bq-saved-query-executor" {
  source      = "github.com/GoogleCloudPlatform/cloud-foundation-fabric/modules/cloud-function-v2"
  project_id  = var.project
  region      = var.region
  name        = "bq-saved-query-executor"
  bucket_name = "${var.project}-bq-saved-query-executor"
  bucket_config = {
    force_destroy = true
  }
  bundle_config = {
    path  = "../functions/data-processing-engines/bq-saved-query-executor"
  }
  function_config = {
    runtime = "python39",
    instance_count = 200
  }
  service_account = module.aef-processing-function-sa.email
}

module "dataform-tag-executor" {
  source      = "github.com/GoogleCloudPlatform/cloud-foundation-fabric/modules/cloud-function-v2"
  project_id  = var.project
  region      = var.region
  name        = "dataform-tag-executor"
  bucket_name = "${var.project}-dataform-tag-executor"
  bucket_config = {
    force_destroy = true
  }
  bundle_config = {
    path  = "../functions/data-processing-engines/dataform-tag-executor"
  }
  function_config = {
    runtime = "python39",
    instance_count = 200
  }
  service_account = module.aef-processing-function-sa.email
}

module "dataflow-flextemplate-job-executor" {
  source      = "github.com/GoogleCloudPlatform/cloud-foundation-fabric/modules/cloud-function-v2"
  project_id  = var.project
  region      = var.region
  name        = "dataflow-flextemplate-job-executor"
  bucket_name = "${var.project}-dataflow-flextemplate-executor"
  bucket_config = {
    force_destroy = true
  }
  bundle_config = {
    path  = "../functions/data-processing-engines/dataflow-flextemplate-job-executor"
  }
  function_config = {
    runtime = "python39",
    instance_count = 200
  }
  service_account = module.aef-processing-function-sa.email
}

module "dataproc-serverless-job-executor" {
  source      = "github.com/GoogleCloudPlatform/cloud-foundation-fabric/modules/cloud-function-v2"
  project_id  = var.project
  region      = var.region
  name        = "dataproc-serverless-job-executor"
  bucket_name = "${var.project}-dataproc-serverless-job-executor"
  bucket_config = {
    force_destroy = true
  }
  bundle_config = {
    path  = "../functions/data-processing-engines/dataproc-serverless-job-executor"
  }
  function_config = {
    runtime = "python39",
    instance_count = 200
  }
  service_account = module.aef-processing-function-sa.email
}