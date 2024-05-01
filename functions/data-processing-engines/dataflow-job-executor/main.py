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
import googleapiclient.discovery
from google.auth.transport.requests import Request

# Authentication Setup - Remains the same
credentials, project = google.auth.default()

@functions_framework.http
def main(request):
    """Triggered by an HTTP request. Extracts parameters, reads a Dataform file (optional),
    and launches a Dataflow batch job.

    Args:
        request: The incoming HTTP request object.

    Returns:
        str: The status of the Dataflow job creation or the job ID (if successful).
    """

    request_json = request.get_json(silent=True)
    dataform_location = request_json['dataform_location']
    dataform_project_id = request_json['dataform_project_id']
    repository_name = request_json['repository_name']
    file_path = request_json.get('file_path', None)  # For optional Dataform integration
    dataflow_template_path = request_json['template_path']
    job_parameters = request_json.get('parameters', {})

    # (Optional) Read Dataform file for additional job configuration if needed
    if file_path:
        dataform_config = read_file(dataform_project_id, dataform_location, repository_name, file_path)
        # ... Process Dataform config and potentially update job_parameters ...

    # Launch the Dataflow job
    status_or_job_id = launch_dataflow_job(project, dataflow_template_path, job_parameters)

    print(f"Dataflow job status: {status_or_job_id}")
    return status_or_job_id


def launch_dataflow_job(project, template_path, job_parameters):
    """Launches a Dataflow batch job.
    Args:
        project (str): The Google Cloud project ID.
        template_path (str): The GCS path to the Dataflow template.
        job_parameters (dict): Parameters to pass to the Dataflow template.

    Returns:
        str: The status of the job launch request or the job ID.
    """

    credentials.refresh(Request())
    dataflow = googleapiclient.discovery.build('dataflow', 'v1b3', credentials=credentials)

    request_body = {
        'jobName': 'your-unique-job-name',  # Replace with a descriptive name
        'parameters': job_parameters,
        'environment': {
            'tempLocation': 'gs://your-dataflow-temp-bucket/temp',
            # Other environment settings if needed
        }
    }

    launch_request = dataflow.projects().templates().launch(
        projectId=project,
        gcsPath=dataflow_template_path,
        body=request_body
    )
    response = launch_request.execute()

    # You'll likely get a response indicating the job is being created; extract the job ID if needed
    return str(response)
