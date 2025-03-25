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

new_repo_name=$1
project_id=$2
working_directory=$3
github_user_name=$4
aef_operator_email=$5
escaped_project_id=$(echo "$project_id" | sed 's/-/\\-/g')

# Check if arguments are provided
if [ -z "$new_repo_name" ] || [ -z "$project_id" ] || [ -z "$working_directory" ] || [ -z "$github_user_name" ] || [ -z "$aef_operator_email" ]; then
  echo "Usage: $0 <new_repo_name> <project_id> <working_directory> <github_user_name> <aef_operator_email>"
  exit 1
fi

if [ ! -d "$working_directory" ] || [[ "${working_directory:0:1}" != "/" ]]; then
  echo "Directory '$working_directory' does not exist. Please set a valid absolute path."
  exit 1
fi

cd $working_directory
if [ -f "aef-orchestration-framework/terraform/tfplanorchframework" ]; then
  echo "Destroying aef-orchestration-framework demo deployment ..."
  cd aef-orchestration-framework/terraform
  terraform destroy -auto-approve -var "project=$project_id" -var "region=us-central1" -var "operator_email=$aef_operator_email" | tee orchfrm_destroy.log
  if grep -qi "error" orchfrm_destroy.log; then
    echo "Terraform destroy failed. Check $working_directory/aef-orchestration-framework/terraform/orchfrm_destroy.log for details. And try again."
    exit 1
  fi
else
  echo "WARNING!: No previous terraform deployment found in aef-orchestration-framework."
  read -r -p "Do you want to skip it and continue? [y/N] " response
  case "$response" in
  [yY][eE][sS] | [yY])
    ;;
  *)
    exit 1
    ;;
  esac
fi

cd $working_directory
if [ -f "aef-data-transformation/terraform/tfplandatatrans" ]; then
  echo "Destroying aef-data-transformation demo deployment ..."
  cd aef-data-transformation/terraform
  terraform destroy -auto-approve -var "project=$project_id" -var 'region=us-central1' -var 'domain=example' -var 'environment=dev' | tee datatrans_destroy.log
  if grep -qi "error" datatrans_destroy.log; then
    echo "Terraform destroy failed. Check $working_directory/aef-data-transformation/terraform/datatrans_destroy.log for details. And try again."
    exit 1
  fi
else
  echo "WARNING!: No previous terraform deployment found in aef-data-transformation."
  read -r -p "Do you want to skip it and continue? [y/N] " response
  case "$response" in
  [yY][eE][sS] | [yY])
    ;;
  *)
    exit 1
    ;;
  esac
fi

cd $working_directory
if [ -f "aef-data-orchestration/terraform/tfplandataorch" ]; then
  cd aef-data-orchestration/terraform
  terraform destroy -auto-approve -var-file="prod.tfvars" | tee dataorch_destroy.log
  if grep -qi "error" dataorch_destroy.log; then
    echo "Terraform destroy failed. Check $working_directory/aef-data-orchestration/terraform/dataorch_destroy.log for details. And try again."
    exit 1
  fi
else
  echo "WARNING!: No previous terraform deployment found in aef-data-orchestration."
  read -r -p "Do you want to skip it and continue? [y/N] " response
  case "$response" in
  [yY][eE][sS] | [yY])
    ;;
  *)
    exit 1
    ;;
  esac
fi

cd $working_directory
if [ -f "aef-data-model/sample-data/terraform/tfplansampledata" ]; then
  echo "Deleting sample dataform repository ..."
  curl -X DELETE -H "Authorization: Bearer $(gcloud auth print-access-token)" "https://dataform.googleapis.com/v1beta1/projects/$project_id/locations/us-central1/repositories/sample-repo-1?force=true"
  echo "Deleting sample Bigquery datasets ..."
  bq rm -r -f -d $project_id:aef_landing_sample_dataset
  bq rm -r -f -d $project_id:aef_curated_sample_dataset
  bq rm -r -f -d $project_id:aef_exposure_sample_dataset

  for ZONE_NAME in $(gcloud dataplex zones list --location=us-central1 --lake=aef-sales-lake --format="value(name)"); do
    for ASSET_NAME in $(gcloud dataplex assets list --zone=$ZONE_NAME --location=us-central1 --lake=aef-sales-lake --format="value(name)"); do
      gcloud dataplex assets delete $ASSET_NAME --location=us-central1 --zone=$ZONE_NAME --lake=aef-sales-lake --quiet
    done
    gcloud dataplex zones delete $ZONE_NAME --location=us-central1 --lake=aef-sales-lake --quiet
  done
  gcloud dataplex lakes delete aef-sales-lake --location=us-central1 --quiet
  gcloud dataplex lakes delete another-sample-lake --location=us-central1 --quiet
  cd aef-data-model/sample-data/terraform/
  terraform destroy -auto-approve -var-file="demo.tfvars" | tee sampledata_destroy.log
  if grep -qi "error" sampledata_destroy.log; then
    echo "Terraform destroy failed. Check $working_directory/aef-data-model/sample-data/terraform/sampledata_destroy.log for details. And try again."
    exit 1
  fi
else
  echo "WARNING!: No previous terraform deployment found in aef-data-model/sample-data."
  read -r -p "Do you want to skip it and continue? [y/N] " response
  case "$response" in
  [yY][eE][sS] | [yY])
    ;;
  *)
    exit 1
    ;;
  esac
fi

cd $working_directory
if [ -f "aef-data-model/terraform/tfplandatamodel" ]; then
  cd aef-data-model/terraform/
  terraform destroy -auto-approve -var-file="prod.tfvars" | tee datamodel_destroy.log
  if grep -qi "error" datamodel_destroy.log; then
    echo "Terraform destroy failed. Check $working_directory/aef-data-orchestration/terraform/datamodel_destroy.log for details. And try again."
    exit 1
  fi
else
  echo "WARNING!:  No previous terraform deployment found in aef-data-model."
  read -r -p "Do you want to skip it and continue? [y/N] " response
  case "$response" in
  [yY][eE][sS] | [yY])
    ;;
  *)
    exit 1
    ;;
  esac
fi