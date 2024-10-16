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

if [ ! -z "$(ls -A $working_directory)" ]; then
  echo "The provided working directory is not empty."
  read -r -p "Do you want to use it anyway? [y/N] " response
  case "$response" in
  [yY][eE][sS] | [yY])
    ;;
  *)
    exit 1
    ;;
  esac
fi

#Fork demo [Dataform repository](https://github.com/oscarpulido55/aef-data-orchestration/blob/0c1a69e655e3435b978e6a68640db141e86b2685/workflow-definitions/demo_pipeline_cloud_workflows.json#L42)
sh set_demo_dataform_repo.sh "$DATAFORM_REPO_NAME" "$PROJECT_ID" "$LOCAL_WORKING_DIRECTORY"

cd $working_directory
if [ ! -f "aef-data-model/sample-data/terraform/tfplansampledata" ]; then
  echo "Deploying demo data sources aef-data-model/sample-data ... "
  git clone git@github.com:oscarpulido55/aef-data-model.git
  cd aef-data-model/sample-data/terraform/
  sed -i.bak "s/<PROJECT_ID>/$escaped_project_id/g" demo.tfvars
  github_dataform_repository="https://github.com/$github_user_name/$new_repo_name.git"
  escaped_github_dataform_repository=$(echo "$github_dataform_repository" | sed 's/-/\\-/g')
  sed -i.bak "s|<GITHUB_DATAFORM_REPOSITORY>|$escaped_github_dataform_repository|g" demo.tfvars
  terraform init
  terraform plan -out=tfplansampledata -var-file="demo.tfvars"
  terraform apply -auto-approve tfplansampledata
  fake_onprem_sql_private_ip=$(terraform output fake_onprem_sql_ip)
else
  echo "WARNING!: There is a previous terraform deployment in aef-data-model/sample-data."
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
if [ ! -f "aef-data-model/terraform/tfplandatamodel" ]; then
  echo "Deploying aef-data-model repository... "
  cd aef-data-model/terraform/
  sed -i.bak "s/<PROJECT_ID>/$escaped_project_id/g" prod.tfvars
  sed -i.bak "s|<GITHUB_DATAFORM_REPOSITORY>|$escaped_github_dataform_repository|g" prod.tfvars
  terraform init
  terraform plan -out=tfplandatamodel -var-file="prod.tfvars"
  terraform apply -auto-approve tfplandatamodel
else
  echo "WARNING!: There is a previous terraform deployment in aef-data-model."
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
if [ ! -f "aef-data-orchestration/terraform/tfplandataorch" ]; then
  echo "Deploying aef-data-orchestration repository... "
  git clone git@github.com:oscarpulido55/aef-data-orchestration.git
  cd aef-data-orchestration/terraform
  sed -i.bak "s/<PROJECT_ID>/$escaped_project_id/g" prod.tfvars
  terraform init
  terraform plan -out=tfplandataorch -var-file="prod.tfvars"
  terraform apply -auto-approve tfplandataorch
else
  echo "WARNING!: There is a previous terraform deployment in aef-data-orchestration."
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
if [ ! -f "aef-data-transformation/terraform/tfplandatatrans" ]; then
  git clone git@github.com:oscarpulido55/aef-data-transformation.git
  sed -i.bak "s/<PROJECT_ID>/$escaped_project_id/g" aef-data-transformation/jobs/dev/dataflow-flextemplate-job-executor/sample_jdbc_dataflow_ingestion.json
  fake_onprem_sql_private_ip=$(gcloud sql instances describe fake-on-prem-instance --format="value(ipAddresses[2].ipAddress)")
  sed -i.bak "s/<DB_PRIVATE_IP>/$fake_onprem_sql_private_ip/g" aef-data-transformation/jobs/dev/dataflow-flextemplate-job-executor/sample_jdbc_dataflow_ingestion.json
  sed -i.bak "s/<PROJECT_ID>/$escaped_project_id/g" aef-data-transformation/jobs/dev/dataform-tag-executor/run_dataform_tag.json
  sed -i.bak "s/<PROJECT_ID>/$escaped_project_id/g" aef-data-transformation/jobs/dev/dataproc-serverless-job-executor/sample_serverless_spark_mainframe_ingestion.json
  sed -i.bak "s/<PROJECT_ID>/$escaped_project_id/g" aef-data-transformation/jobs/dev/dataproc-serverless-job-executor/cobrix/example_cobrix_job.json
  cd aef-data-transformation/terraform
  terraform init
  terraform plan -out=tfplandatatrans -var "project=$project_id" -var 'region=us-central1' -var 'domain=example' -var 'environment=dev'
  terraform apply -auto-approve tfplandatatrans
else
  echo "WARNING!: There is a previous terraform deployment in aef-data-transformation."
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
if [ ! -f "aef-orchestration-framework/terraform/tfplanorchframework" ]; then
  git clone git@github.com:oscarpulido55/aef-orchestration-framework.git
  cd aef-orchestration-framework/terraform
  terraform init
  terraform plan -out=tfplanorchframework -var "project=$project_id" -var "region=us-central1" -var "operator_email=$aef_operator_email"
  terraform apply -auto-approve tfplanorchframework
else
  echo "WARNING!: There is a previous terraform deployment in aef-orchestration-framework, skipping it ... "
fi
