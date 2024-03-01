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

module "cf_bigquery_executor" {
  source      = "github.com/GoogleCloudPlatform/cloud-foundation-fabric/modules/cloud-function-v2"
  project_id  = var.project
  region      = var.region
  name        = "cf_bigquery_executor"
  bucket_name = var.bucket_name
    bucket_config = {
    lifecycle_delete_age_days = 1
  }
  bundle_config = {
    source_dir  = "../functions/data-processing-engines/bigquery-executor"
    output_path = "bundle.zip"
  }
  function_config = {
    runtime = "python39"
  }
}