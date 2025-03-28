terraform {
  backend "gcs" {
    bucket = "<TERRAFORM_BUCKET>"
    prefix = "<TERRAFORM_ENV>"
  }
}