# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
from google.cloud import bigquery
from datetime import datetime
import google.auth
import urllib
import json
import google.auth.transport.requests
import google.oauth2.id_token

# Access environment variables
WORKFLOW_CONTROL_PROJECT_ID = os.environ.get('WORKFLOW_CONTROL_PROJECT_ID')
WORKFLOW_CONTROL_DATASET_ID = os.environ.get('WORKFLOW_CONTROL_DATASET_ID')
WORKFLOW_CONTROL_TABLE_ID = os.environ.get('WORKFLOW_CONTROL_TABLE_ID')

SIMPLE_DATAFORM_QUERY_EXECUTOR_URL = os.environ.get('SIMPLE_DATAFORM_QUERY_EXECUTOR_URL')
DATAFORM_LOCATION = os.environ.get('DATAFORM_LOCATION')
DATAFORM_PROJECT = os.environ.get('DATAFORM_PROJECT')
DATAFORM_REPO_NAME = os.environ.get('DATAFORM_REPO_NAME')

# define clients
bq_client = bigquery.Client(project=WORKFLOW_CONTROL_PROJECT_ID)

def main(request):
    request_json = request.get_json()
    print("event: " + str(request_json))
    if request_json and 'call_type' in request_json:
        call_type = request_json['call_type']
    else:
        return f'no call type!'

    if call_type == "get_id":
        return call_custom_function(request_json, None)
    elif call_type == "get_status":
        if request_json and 'async_job_id' in request_json:
            log_job_id(request_json['async_job_id'])
            status = call_custom_function(request_json, request_json['async_job_id'])
        else:
            return f'Job Id not received!'
        log_step_bigquery(request_json, status)
        return status
    else:
        return f'Invalid call type!'


def log_job_id(async_job_id):
    print(f"Executing Async Job ID: {async_job_id}")


def log_step_bigquery(request_json, status):
    current_datetime = datetime.now().isoformat()
    data = {
        'workflow_execution_id': request_json['execution_id'],
        'workflow_name': request_json['workflow_name'],
        'job_name': request_json['job_name'],
        'job_status': status,
        'start_date': current_datetime,
        'end_date': current_datetime,
        'error_code': '0',
        'job_params': '',
        'log_path': '',
        'retry_count': 0,
        'execution_time_seconds': 0,
        'message': ''
    }

    workflows_control_table = bq_client.dataset(WORKFLOW_CONTROL_DATASET_ID).table(WORKFLOW_CONTROL_TABLE_ID)
    errors = bq_client.insert_rows_json(workflows_control_table, [data])  # Use list for multiple inserts
    if not errors:
        print("New row has been added.")
    else:
        print("Encountered errors while inserting row: {}".format(errors))


def call_custom_function(request_json, async_job_id):
    workflow_name = request_json['workflow_name']
    job_name = request_json['job_name']
    params = {
        "dataform_location": DATAFORM_LOCATION,
        "dataform_project_id": DATAFORM_PROJECT,
        "repository_name": DATAFORM_REPO_NAME,
        "file_path": "definitions/" + workflow_name + "/" + job_name + ".sqlx",
        "query_variables": {
            "${dataform.projectConfig.vars.start_date}": request_json['query_variables']['start_date'],
            "${dataform.projectConfig.vars.end_date}": request_json['query_variables']['end_date']
        }
    }

    if async_job_id:
        params['job_id'] = async_job_id

    req = urllib.request.Request(SIMPLE_DATAFORM_QUERY_EXECUTOR_URL, data=json.dumps(params).encode("utf-8"))

    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, SIMPLE_DATAFORM_QUERY_EXECUTOR_URL)

    req.add_header("Authorization", f"Bearer {id_token}")
    req.add_header("Content-Type", "application/json")
    response = urllib.request.urlopen(req)
    response = response.read()

    print('response: ' + str(response))
    # Handle the response

    if async_job_id == None and response.decode("utf-8").startswith("aef_"):
        return response.decode("utf-8")
    if response.decode("utf-8") in ('DONE', 'SUCCESS'):
        return "success"
    if response.decode("utf-8") in ('PENDING', 'RUNNING'):
        return "running"
    else:  # FAILURE
        return f"Error calling target function: {response.decode('utf-8')}"
