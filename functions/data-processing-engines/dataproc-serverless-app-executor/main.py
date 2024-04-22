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
import google.auth
import functions_framework
import requests
import base64
import uuid
import datetime
import os
import json
from google.api_core.exceptions import BadRequest
from google.auth.transport.requests import Request

# --- Authentication Setup ---
credentials, project = google.auth.default()

BIGQUERY_PROJECT = os.environ.get('BIGQUERY_PROJECT')

@functions_framework.http
def main(request):
    """
    Main function, likely triggered by an HTTP request. Extracts parameters, executes a dataproc serverless job
    , and reports the result status or job ID.

    Args:
        request: The incoming HTTP request object.

    Returns:
        str: The status of the query execution or the job ID (if asynchronous).
    """

    request_json = request.get_json(silent=True)
    print("event:" + str(request_json))

    try:
        workflow_properties= request_json.get('workflow_properties', None)
        workflow_name = request_json.get('workflow_name')
        job_name = request_json.get('job_name')
        query_variables = request_json.get('query_variables', None)
        job_id = request_json.get('job_id', None)

        status_or_job_id = execute_job_or_get_status(job_id, workflow_name, job_name, query_variables, workflow_properties)

        if status_or_job_id.startswith('aef-'):
            print(f"Running Job, track it with Job ID: {status_or_job_id}")
        else:
            print(f"Call finished with status: {status_or_job_id}")

        return status_or_job_id
    except Exception as error:
        err_message = "Exception: " + repr(error)
        print(err_message)
        response = {
            "error": error.__class__.__name__,
            "message": repr(error)
        }
        return response


def execute_job_or_get_status(job_id, workflow_name, job_name, query_variables, workflow_properties):
    if job_id:
        return get_job_status(job_id, workflow_properties)
    else:
        return create_batch_job(workflow_name, job_name, query_variables, workflow_properties)


def create_batch_job(workflow_name, job_name, query_variables, workflow_properties):
    """
    calls a dataproc serverless job.

    Args:
        request_json (dict) : event dictionary
    Returns:
        str: Id or status of the dataproc serverless batch job
    """

    dataproc_serverless_project_id= workflow_properties.get('dataproc_serverless_project_id')
    dataproc_serverless_region= workflow_properties.get('dataproc_serverless_region')
    jar_file_location= workflow_properties.get('jar_file_location')
    spark_history_server_cluster= workflow_properties.get('spark_history_server_cluster')
    spark_app_main_class= workflow_properties.get('spark_app_main_class')
    spark_app_config_bucket= workflow_properties.get('spark_app_config_bucket')
    dataproc_serverless_runtime_version= workflow_properties.get('dataproc_serverless_runtime_version')
    spark_app_properties= workflow_properties.get('spark_app_properties')
    spark_history_server_cluster_path = f"projects/{dataproc_serverless_project_id}/regions/{dataproc_serverless_region}/clusters/{spark_history_server_cluster}"

    if isinstance(spark_app_properties, str):
        spark_app_properties = json.loads(spark_app_properties)

    credentials.refresh(Request())
    headers = {"Authorization": f"Bearer {credentials.token}"}

    curr_dt = datetime.datetime.now()
    timestamp = int(round(curr_dt.timestamp()))

    params={
        "spark_batch": {
            "jar_file_uris": [ jar_file_location ],
            "main_class": spark_app_main_class,
            "args": [
                spark_app_config_bucket + "/" + workflow_name + "/" + job_name + ".json"
            ]
        },
        "runtime_config": {
            "version": dataproc_serverless_runtime_version,
            "properties": spark_app_properties
        },
        "environment_config": {
            "peripherals_config": {
                "spark_history_server_config": {
                    "dataproc_cluster": spark_history_server_cluster_path
                },
            },
        },

    }

    print(params)

    batch_id = f"aef-{timestamp}"

    url = (f"https://dataproc.googleapis.com/v1/projects/{dataproc_serverless_project_id}/"
           f"locations/{dataproc_serverless_region}/batches?batchId={batch_id}")

    response = requests.post(url, json=params, headers=headers)

    if response.status_code == 200:
        print("response::" + str(response))
        return batch_id
    else:
        error_message = f"Dataproc API CREATE request failed. Status code:{response.status_code}"
        print(error_message)
        print(response.text)
        raise Exception(error_message)



def get_job_status(job_id, workflow_properties):
    """
    gets the status of a dataproc serverless job

    Args:
        request_json (dict) : event dictionary
    Returns:
        str: status of the dataproc serverless batch job
    """

    dataproc_serverless_project_id= workflow_properties.get('dataproc_serverless_project_id')
    dataproc_serverless_region= workflow_properties.get('dataproc_serverless_region')

    credentials.refresh(Request())
    headers = {"Authorization": f"Bearer {credentials.token}"}

    url = (f"https://dataproc.googleapis.com/v1/projects/{dataproc_serverless_project_id}/"
           f"locations/{dataproc_serverless_region}/batches/{job_id}")

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("response::" + str(response))
        return response.json().get("state")
    else:
        error_message = f"Dataproc API GET request failed. Status code:{response.status_code}"
        print(error_message)
        print(response.text)
        raise Exception(error_message)