module "aef-processing-functino-sa" {
  source     = "github.com/GoogleCloudPlatform/cloud-foundation-fabric/modules/iam-service-account"
  project_id = var.project
  name       = "aef-processing-functino-sa"

  # non-authoritative roles granted *to* the service accounts on other resources
  iam_project_roles = {
    "${var.project}" = [
      "roles/editor",
      "roles/secretmanager.secretAccessor"
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
    source_dir  = "../functions/data-processing-engines/bq-saved-query-executor"
    output_path = "bundle-bq-saved-query-executor.zip"
  }
  function_config = {
    runtime = "python39"
  }
  service_account = module.aef-processing-functino-sa.email
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
    source_dir  = "../functions/data-processing-engines/dataform-tag-executor"
    output_path = "bundle-dataform-tag-executor.zip"
  }
  function_config = {
    runtime = "python39"
  }
  service_account = module.aef-processing-functino-sa.email
}

module "dataproc-serverless-app-executor" {
  source      = "github.com/GoogleCloudPlatform/cloud-foundation-fabric/modules/cloud-function-v2"
  project_id  = var.project
  region      = var.region
  name        = "dataproc-serverless-app-executor"
  bucket_name = "${var.project}-dataproc-serverless-app-executor"
  bucket_config = {
    force_destroy = true
  }
  bundle_config = {
    source_dir  = "../functions/data-processing-engines/dataproc-serverless-app-executor"
    output_path = "bundle-dataproc-serverless-app-executor.zip"
  }
  function_config = {
    runtime = "python39"
  }
  service_account = module.aef-processing-functino-sa.email
}