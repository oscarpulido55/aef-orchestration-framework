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
import grpc
import requests
import base64
import uuid
import re
import os
from google.cloud import bigquery, dataform_v1beta1, resourcemanager_v3
from google.api_core.exceptions import BadRequest
from google.auth.transport.requests import Request

# --- Authentication Setup ---
credentials, project = google.auth.default()

BIGQUERY_PROJECT = os.environ.get('BIGQUERY_PROJECT')


@functions_framework.http
def main(request):
    """
    Main function, likely triggered by an HTTP request. Extracts parameters, reads a BigQuery saved query
    (backed by Dataform),executes the file's contents as a BigQuery query, and reports the result status or job ID.

    Args:
        request: The incoming HTTP request object.

    Returns:
        str: The status of the query execution or the job ID (if asynchronous).
    """

    request_json = request.get_json(silent=True)
    print("event:" + str(request_json))

    try:
        dataform_location = request_json['workflow_properties']['dataform_location']
        dataform_project_id = request_json['workflow_properties']['dataform_project_id']
        repository_name = request_json['workflow_properties']['repository_name']
        workflow_name = request_json['workflow_name']
        job_name = request_json['job_name']
        file_path = f"definitions/{workflow_name}/{job_name}.sqlx"

        job_id = request_json.get('job_id', None)
        query_variables = request_json.get('query_variables', None)

        query_file = read_file(dataform_project_id, dataform_location, repository_name, file_path, query_variables)
        status_or_job_id = execute_query_or_get_status(query_file, file_path, job_id)

        if status_or_job_id.startswith('aef_'):
            print(f"Running Query, track it with Job ID: {status_or_job_id}")
        else:
            print(f"Query finished with status: {status_or_job_id}")

        return status_or_job_id
    except Exception as error:
        err_message = "Exception: " + repr(error)
        response = {
            "error": error.__class__.__name__,
            "message": repr(error)
        }
        return response


def read_file(project_id, location, repository_name, file_path, query_variables):
    """
    Reads a file from a Google Dataform repository and optionally replaces variables.

    Args:
        project_id (str): The Google Cloud project ID.
        location (str): The Dataform repository's location.
        repository_name (str): The name of the Dataform repository.
        file_path (str): The path to the file within the repository.
        query_variables (dict): A dictionary for variable replacement (optional).

    Returns:
        str: The file's contents if successful, otherwise None.
    """
    credentials.refresh(Request())
    headers = {"Authorization": f"Bearer {credentials.token}"}

    url = (f"https://dataform.googleapis.com/v1beta1/projects/{project_id}/"
           f"locations/{location}/repositories/{repository_name}:"
           f"readFile?path={file_path}")
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        file_contents = base64.b64decode(response.json()["contents"]).decode('utf-8').lstrip("-n")
        if query_variables:
            file_contents = replace_variables(file_contents, query_variables)
        if file_contents.startswith("config"):
            file_contents = file_contents.split("\n", 3)[3]
        return file_contents
    else:
        error_message = f"Dataform API request failed. Status code:{response.status_code}"
        print(error_message)
        print(response.text)
        raise Exception(error_message)


def execute_query_or_get_status(query_file, file_path, job_id=None):
    """Executes a BigQuery query (if job ID not provided) or gets the status of an existing query.
    Args:
        query_file (str): The Dataform query to execute.
        job_id (str, optional): The ID of an existing BigQuery job. Defaults to None.
    Returns:
        str: The final state of the query job ('DONE', 'FAILED', etc.) or the query job ID if the query times out.
    """
    client = bigquery.Client(project=BIGQUERY_PROJECT)
    if job_id:
        query_job = client.get_job(job_id)
        print(f"Checking status of existing job: {job_id}")
        if query_job.done():
            if query_job.error_result:
                raise BadRequest(query_job.error_result)
            return query_job.state
        else:
            print(f"Query still running in state:{str(query_job.state)}")
            return query_job.state
    else:
        job_id = f"aef_{transform_string(file_path)}_{uuid.uuid4()}"
        job_config = bigquery.QueryJobConfig(
            priority=bigquery.QueryPriority.BATCH
        )
        query_job = client.query(query=query_file, job_config=job_config, job_id=job_id)
        print(f"New query started. Job ID: {query_job.job_id}")
        return query_job.job_id


def transform_string(text):
    """
    Transforms a string by removing non-alphanumeric characters (except spaces and hyphens)
    and replacing spaces with underscores, then trims any leading or trailing underscores or hyphens.

    Args:
        text (str): The input string to transform.

    Returns:
        str: The transformed string.
    """
    temp_text = re.sub(r"[^\w\s-]", " ", text)
    temp_text = re.sub(r"\s+", "_", temp_text)
    transformed_text = temp_text.strip("_-")
    return transformed_text


def replace_variables(file_contents, query_variables):
    """
    Replaces variables in a string with their corresponding values from a dictionary.

    Args:
        file_contents (str): The string containing the variables to be replaced.
        query_variables (dict): A dictionary mapping variable names to their values.

    Returns:
        str: The string with the variables replaced.
    """
    for key, value in query_variables.items():
        file_contents = file_contents.replace(key, f"'{value}'")
    return file_contents
