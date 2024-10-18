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

working_directory=$1
project_id=$2

# Check if arguments are provided
if [ -z "$project_id" ] || [ -z "$working_directory" ]; then
  echo "Usage: $0<project_id> <working_directory>"
  exit 1
fi

if [ ! -d "$working_directory" ] || [[ "${working_directory:0:1}" != "/" ]]; then
  echo "Directory '$working_directory' does not exist. Please set a valid absolute path."
  exit 1
fi

cd $working_directory
python3 -m venv .firestorevenv
source .firestorevenv/bin/activate
python3 -m pip install google-cloud
python3 -m pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
python3 -m pip install --upgrade google-cloud-firestore

region=us-central1
workflow_name=demo_pipeline_cloud_workflows

workflow_properties='{"location":"'$region'","project_id":"'$project_id'"}'

python3 aef-orchestration-framework/functions/orchestration-helpers/scheduling/utilities/firestore_crud.py --gcp_project $project_id \
                          --workflow_name $workflow_name \
                          --operation_type CREATE \
                          --crond_expression '0 7 * * *' \
                          --time_zone 'America/Los_Angeles' \
                          --date_format '%Y-%m-%d' \
                          --workflow_status ENABLED \
                          --workflow_properties $workflow_properties