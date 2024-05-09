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
}