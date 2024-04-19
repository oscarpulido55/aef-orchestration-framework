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


module "dataproc-serverless-app-executor" {
  source      = "github.com/GoogleCloudPlatform/cloud-foundation-fabric/modules/cloud-function-v2"
  project_id  = var.project
  region      = var.region
  name        = "orch-framework-dataproc-serverless-app-executor"
  bucket_name = "${var.project}-dataproc-serverless-app-executor-bucket"
  bucket_config = {
    force_destroy = true
  }
  bundle_config = {
    source_dir  = "../functions/data-processing-engines/dataproc-serverless-app-executor"
    output_path = "bundle-orch-framework-dataproc-serverless-app-executor.zip"
  }
  function_config = {
    runtime = "python39"
  }
}