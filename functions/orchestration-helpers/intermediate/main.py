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
import re
import google.auth
import urllib
import urllib.error
import urllib.request
import json
import logging
import google.auth.transport.requests
import functions_framework
import google.oauth2.id_token
from google.cloud import bigquery
from datetime import datetime, timedelta
from google.cloud import error_reporting
from enum import Enum
from urllib import parse

# Access environment variables
WORKFLOW_CONTROL_PROJECT_ID = os.environ.get('WORKFLOW_CONTROL_PROJECT_ID')
WORKFLOW_CONTROL_DATASET_ID = os.environ.get('WORKFLOW_CONTROL_DATASET_ID')
WORKFLOW_CONTROL_TABLE_ID = os.environ.get('WORKFLOW_CONTROL_TABLE_ID')

# define clients
bq_client = bigquery.Client(project=WORKFLOW_CONTROL_PROJECT_ID)
error_client = error_reporting.Client()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class JobStatus(Enum):
    SUCCESS = ("DONE", "SUCCESS", "SUCCEEDED", "JOB_STATE_DONE")
    RUNNING = ("PENDING", "RUNNING", "JOB_STATE_QUEUED", "JOB_STATE_RUNNING", "JOB_STATE_PENDING")


@functions_framework.http
def main(request):
    """
    Main function, likely triggered by an HTTP request from cloud workflows.
    Acts as an intermediary between workflows and executor functions, taking care of the
    non-functional requirements as process metadata creation , error handling, notifications management,
    checkpoint management, etc.

    Args:
        request: The incoming HTTP request object.

    Returns:
        str: The status of the query execution or the job ID (if asynchronous).
    """
    request_json = request.get_json()
    print("event: " + str(request_json))
    try:
        if request_json and 'call_type' in request_json:
            call_type = request_json['call_type']
        else:
            Exception("No call type!")
        if call_type == "get_id":
            get_id_result = evaluate_error(call_custom_function(request_json, None))
            status = 'started' if is_valid_step_id(get_id_result) else 'failed_start'
            log_step_bigquery(request_json, status)
            return get_id_result
        elif call_type == "get_status":
            if request_json and 'async_job_id' in request_json:
                status = evaluate_error(call_custom_function(request_json, request_json['async_job_id']))
            else:
                Exception("Job Id not received!")
            return status
        else:
            raise Exception("Invalid call type!")
    except Exception as ex:
        exception_message = "Exception : " + repr(ex)
        # TODO register error in checkpoint table
        error_client.report_exception()
        logger.error(exception_message)
        print(RuntimeError(repr(ex)))
        return exception_message, 500


def is_valid_step_id(step_id):
    """Checks if a step ID starts with "aef_" or "aef-".

    Args:
        step_id: The step ID string to check.

    Returns:
        True if the step ID is valid, False otherwise.
    """

    pattern = r"^aef[_-]"  # Use a regular expression for more flexibility
    return bool(re.match(pattern, step_id))


def evaluate_error(message):
    """
    Evaluates if a message has an error

    Args:
        str: message to evaluate

    Returns:
        raise Exception if the word "exception" found in message
        str: original message coming from executor functions
        :param message:
    """
    if 'error' in message.lower() or 'exception' in message.lower():
        raise Exception(message)
    return message


def log_step_bigquery(request_json, status):
    """
    Logs a new entry in workflows bigquery table on finished or started step, ether it failed of succeed

    Args:
        status: status of the execution
        request_json: event object containing info to log

    """
    target_function_url = request_json['function_url_to_call']
    current_datetime = datetime.now().isoformat()
    status_to_error_code = {
        'success': '0',
        'started': '0',
        'failed_start': '1',
        'failed': '2'
    }
    data = {
        'workflow_execution_id': request_json['execution_id'],
        'workflow_name': request_json['workflow_name'],
        'job_name': request_json['job_name'],
        'job_status': status,
        'timestamp': current_datetime,
        'error_code': status_to_error_code.get(status, '2'),
        'job_params': str(request_json),
        'log_path': get_cloud_logging_url(target_function_url),
        'retry_count': 0  # TODO
    }

    workflows_control_table = bq_client.dataset(WORKFLOW_CONTROL_DATASET_ID).table(WORKFLOW_CONTROL_TABLE_ID)
    errors = bq_client.insert_rows_json(workflows_control_table, [data])
    if not errors:
        print("New row has been added.")
    else:
        raise Exception("Encountered errors while inserting row: {}".format(errors))


def get_cloud_logging_url(target_function_url):
    """
    Retrieves the Cloud Logging URL for the most recent execution of a specified Google Cloud Function.

    Args:
        target_function_url (str): The URL of the target Google Cloud Function.

    Returns:
        str: The Cloud Logging URL for the most recent execution of the function,
             or None if no matching log entries are found.
    """
    date = datetime.utcnow() - timedelta(minutes=59)
    function_name = target_function_url.split('/')[-1]

    # Remove newline characters and extra whitespace from the filter string
    filter_str = f"""
        (resource.type="cloud_function" AND resource.labels.function_name="{function_name}") 
        OR 
        (resource.type="cloud_run_revision" AND resource.labels.function_name="{function_name}") 
        AND timestamp>="{date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")}" 
    """
    filter_str = ' '.join(filter_str.split())  # Remove extra whitespace

    # Then apply the double URL encoding (TODO enhance encoding to get URL link)
    encoded_filter = parse.quote(parse.quote(filter_str, safe=''), safe='')
    encoded_filter = (
        encoded_filter
        .replace('%253D%2522', '%20%3D%20%22')
        .replace("%2522%2520", "%22%0A%20")
        .replace("%2520", "%20")
        .replace("%2522%2529%20", "%22%2529%0A%20")
        .replace("%253E%20%3D%20%", "%3E%3D%")
        .replace("%253A", ":")
        .replace("Z%2522", "Z%22")
    )
    base_url = "https://console.cloud.google.com/logs/query"
    query_params = f";query={encoded_filter}"
    log_url = f"{base_url}{query_params}"
    print("Cloud Logging URL query:", log_url)
    return log_url


def call_custom_function(request_json, async_job_id):
    """
    calls an executor function passed by parameter

    Args:
        request_json: json input object with parameters
        async_job_id: if filled, function ask by the execution status. if not, launches the execution for the first time

    Returns:
        raise Exception if the word "exception" is found in message
        str: original message coming from executor functions
    """
    workflow_name = request_json['workflow_name']
    job_name = request_json['job_name']
    workflow_properties = request_json.get('workflow_properties')
    step_properties = request_json.get('step_properties')
    workflow_properties = join_properties(workflow_properties, step_properties)

    params = {
        "workflow_properties": workflow_properties,
        "workflow_name": workflow_name,
        "job_name": job_name,
        "query_variables": {
            "start_date": "'" + request_json['query_variables']['start_date'] + "'",
            "end_date": "'" + request_json['query_variables']['end_date'] + "'"
        }
    }

    if async_job_id:
        params['job_id'] = async_job_id

    target_function_url = request_json['function_url_to_call']
    try:
        req = urllib.request.Request(target_function_url, data=json.dumps(params).encode("utf-8"))

        auth_req = google.auth.transport.requests.Request()
        id_token = google.oauth2.id_token.fetch_id_token(auth_req, target_function_url)

        req.add_header("Authorization", f"Bearer {id_token}")
        req.add_header("Content-Type", "application/json")
        response = urllib.request.urlopen(req)
        response = response.read()

        print('response: ' + str(response))
        final_response = ''
        # Handle the response
        decoded_response = response.decode("utf-8")
        if async_job_id is None and is_valid_step_id(decoded_response):
            final_response = decoded_response
        elif decoded_response in JobStatus.SUCCESS.value:
            final_response = "success"
            log_step_bigquery(request_json, final_response)
        elif decoded_response in JobStatus.RUNNING.value:
            final_response = "running"
        else:  # FAILURE
            final_response = f"Exception calling target function {target_function_url.split('/')[-1]}:{decoded_response}"
            log_step_bigquery(request_json, "failed")
        print("final response: " + final_response)
        return final_response
    except (urllib.error.HTTPError) as e:
        print('Exception: ' + repr(e))
        raise Exception(
            "Unexpected error in custom function: " + target_function_url.split('/')[-1] + ":" + repr(e))


def join_properties(workflow_properties, step_properties):
    """
    receives 2 dictionaries if exists, and join step properties into workflow properties, overriding props if necessary.

    Args:
        workflow_properties: properties passed in firestore to the workflow
        step_properties: properties configured in each step in functional json workflow definition.
                         can overwrite workflow properties

    Returns:
        final properties dictionary
    """

    # Handle None or empty inputs
    workflow_props = {}
    if workflow_properties:
        workflow_props = json.loads(workflow_properties) if isinstance(workflow_properties,
                                                                       str) else workflow_properties

    step_props = {}
    if step_properties:
        step_props = json.loads(step_properties) if isinstance(step_properties, str) else step_properties

    return {**workflow_props, **step_props}
