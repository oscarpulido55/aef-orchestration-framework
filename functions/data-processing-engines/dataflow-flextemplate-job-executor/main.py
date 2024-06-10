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
from googleapiclient.discovery import build
import json
from google.cloud import storage
import re
import os

# --- Authentication Setup ---
credentials, project = google.auth.default()
# --- Dataflow Client ---
service = build('dataflow', 'v1b3', credentials=credentials)
storage_client = storage.Client()
function_name = os.environ.get('K_SERVICE')

# df_client = dataflow.FlexTemplatesServiceClient()


@functions_framework.http
def main(request):
    """
    Cloud Function entry point for handling Dataflow job requests.

    This function processes an incoming HTTP request, extracting details about a Dataflow Flex Template job.
    It either launches a new Dataflow job or retrieves the status of an existing job based on the request.

    Args:
        request: The incoming HTTP request object.  Expected to contain a JSON payload with the following keys:
            - workflow_properties: A dictionary containing Dataflow job configuration:
                - dataflow_location: The GCP region for the Dataflow job.
                - dataflow_project_id: The GCP project ID for the Dataflow job.
                - dataflow_template_gcs_path: The GCS path to the Dataflow Flex Template.
                - dataflow_job_name: The name to assign to the Dataflow job.
                - dataflow_job_params: (Optional) A dictionary of parameters for the Dataflow job.
            - workflow_name: The name of the workflow triggering the Dataflow job.
            - job_name:  A unique identifier for the job within the workflow.
            - job_id: (Optional) The ID of an existing Dataflow job (if checking status).

    Returns:
        str:
            - If launching a new job: The Dataflow job ID (prefixed with "aef_").
            - If getting job status: The current state of the Dataflow job (e.g., "JOB_STATE_RUNNING").
            - If an error occurs: A JSON object with error details.
    """
    request_json = request.get_json(silent=True)
    print("event:" + str(request_json))

    try:
        dataflow_location = request_json.get('workflow_properties').get('location', None)
        dataflow_project_id = request_json.get('workflow_properties').get('project_id', None)

        job_name = request_json.get("job_name", "")
        dataflow_job_name = re.sub(r"^\d+", "", re.sub(r"[^a-z0-9+]", "", request_json.get("job_name", "")))
        dataflow_job_name = re.sub(r"^\d+", "", dataflow_job_name)

        job_id = request_json.get('job_id', None)
        workflow_name = request_json.get('workflow_name', None)

        status_or_job_id = run_dataflow_job_or_get_status(job_id, gcp_project=dataflow_project_id,
                                                          location=dataflow_location,
                                                          dataflow_job_name=dataflow_job_name,
                                                          job_name=job_name,
                                                          request_json=request_json)

        if status_or_job_id.startswith('aef_'):
            print(f"Running Dataflow Job, track it with Job ID: {status_or_job_id}")
        else:
            print(f"Dataflow Job with status: {status_or_job_id}")

        return status_or_job_id
    except Exception as error:
        err_message = "Exception: " + repr(error)
        response = {
            "error": error.__class__.__name__,
            "message": repr(err_message)
        }
        return response


def extract_dataflow_params(bucket_name, job_name, function_name, encoding='utf-8'):
    """Extracts Dataflow parameters from a JSON file.

    Args:
        bucket_name: Bucket containing the JSON parameters file .

    Returns:
        A dictionary containing the extracted Dataflow parameters.
    """

    json_file_path = f'gs://{bucket_name}/{function_name}/{job_name}.json'

    parts = json_file_path.replace("gs://", "").split("/")
    bucket_name = parts[0]
    object_name = "/".join(parts[1:])
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(object_name)

    json_data = blob.download_as_bytes()
    params = json.loads(json_data.decode(encoding))
    return params


def run_dataflow_job_or_get_status(job_id: str, gcp_project: str, location: str,
                                   dataflow_job_name: str, job_name:str, request_json):

    request_json = request_json
    if job_id:
        return get_dataflow_state(job_id, gcp_project, location)
    else:
        return run_dataflow_job(gcp_project, location, dataflow_job_name, job_name, request_json)


def run_dataflow_job(gcp_project, location, dataflow_job_name, job_name, request_json):

    extracted_params = extract_dataflow_params(
        bucket_name=request_json.get("workflow_properties").get("jobs_definitions_bucket"),
        job_name=job_name,
        function_name=function_name
    )

    dataflow_template_name = extracted_params.get("dataflow_template_name")
    dataflow_temp_bucket = extracted_params.get("dataflow_temp_bucket")
    dataflow_job_params = extracted_params.get("dataflow_job_params")
    dataflow_max_workers = extracted_params.get("dataflow_max_workers")
    network = extracted_params.get("network")
    subnetwork = extracted_params.get("subnetwork")
    dataflow_template_version = extracted_params.get("dataflow_template_version")

    gcs_path = "gs://dataflow-templates-{region}/{version}/flex/{template}".format(region=location,
                                                                                   version=dataflow_template_version,
                                                                                   template=dataflow_template_name)
    body = {
        "launchParameter": {
            "jobName": dataflow_job_name,
            "parameters": dataflow_job_params,
            "containerSpecGcsPath": gcs_path,
            "environment": {"tempLocation": "gs://{bucket}/dataflow/temp".format(bucket=dataflow_temp_bucket),
                            "maxWorkers": str(dataflow_max_workers),
                            "network": str(network),
                            "subnetwork": str(subnetwork)}
        }
    }

    request = service.projects().locations().flexTemplates().launch(
        projectId=gcp_project,
        location=location,
        body=body
    )
    response = request.execute()
    return "aef_"+response.get("job").get("id")


def get_dataflow_state(job_id, gcp_project, location):
    get_job_request = service.projects().locations().jobs().get(location=location,projectId=gcp_project, jobId=re.sub(r"^aef_", "", job_id))

    print("Getting status execute ")
    job_status = get_job_request.execute()

    print(f"Job status: {str(job_status)}")

    return job_status['currentState']