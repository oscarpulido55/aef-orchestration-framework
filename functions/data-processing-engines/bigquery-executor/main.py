import google.auth
import functions_framework
import grpc
import time
import requests
import base64
import uuid
import re
from google.cloud import bigquery, dataform_v1beta1
from google.api_core.exceptions import BadRequest
from google.auth.transport.requests import Request

# --- Authentication Setup ---
credentials, project = google.auth.default()

@functions_framework.http
def main(request):
    request_json = request.get_json(silent=True)

    location = request_json['location']
    project_id = request_json['project_id']
    repository_name = request_json['repository_name']
    file_path = request_json['file_path']

    try:
        job_id = request_json['job_id']
    except:
        job_id = None

    query_file = read_file(project_id, location, repository_name, file_path)
    status_or_job_id = execute_query_or_get_status(project_id, query_file, file_path, job_id)
    if status_or_job_id.startswith('aef_'):
        print(f"Long running Query, track it with Job ID: {status_or_job_id}")
    else:
        print(f"Query finished with status: {status_or_job_id}")

    return status_or_job_id


def read_file(project_id, location, repository_name, file_path):
    credentials.refresh(Request())
    headers = {"Authorization": f"Bearer {credentials.token}"}

    url = (f"https://dataform.googleapis.com/v1beta1/projects/{project_id}/"
           f"locations/{location}/repositories/{repository_name}:"
           f"readFile?path={file_path}")
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        file_contents = base64.b64decode(response.json()["contents"]).decode('utf-8')
        print(file_contents)
        return file_contents
    else:
        print("API request failed. Status code:", response.status_code)
        print(response.text)
        return None


def read_file_grpc(project_id, location, repository_name, file_path, commit_sha=None):
    """Reads a file from a Dataform repository using a hypothetical gRPC method.
    Args:
        project_id (str): Your Google Cloud project ID.
        location (str): The location of the repository (e.g., 'us-central1').
        repository_name (str): The name of the repository.
        file_path (str): The full path to the file within the repository.
        commit_sha (str, optional): The commit SHA to read from.
    Returns:
        dataform_v1beta1.ReadFileResponse:  The response object, containing the file contents, if successful.  Otherwise, None.
    """
    try:
        channel = grpc.secure_channel('dataform.googleapis.com', grpc.ssl_channel_credentials())
        stub = dataform_v1beta1.RepositoryServiceStub(channel)
        request = dataform_v1beta1.ReadFileRequest(
            workspace=f"projects/{project_id}/locations/{location}/repositories/{repository_name}",
            path=file_path
        )
        response = stub.ReadFile(request)
        print(response.file_contents)
        return response

    except grpc.RpcError as e:
        print(f"gRPC error occurred: {e}")
        return None

def execute_query_or_get_status(project_id, query_file, file_path, job_id=None):
    """Executes a BigQuery query (if job ID not provided) or gets the status of an existing query.
    Args:
        query_file (str): The Dataform query to execute.
        job_id (str, optional): The ID of an existing BigQuery job. Defaults to None.
    Returns:
        str: The final state of the query job ('DONE', 'FAILED', etc.) or the query job ID if the query times out.
    """
    client = bigquery.Client(project_id, credentials)
    timeout = 60

    if job_id:
        query_job = client.get_job(job_id)
        print(f"Checking status of existing job: {job_id}")
    else:
        job_id = f"aef_{transform_string(file_path)}_{uuid.uuid4()}"
        query_job = client.query(query_file, job_id=job_id)
        print(f"New query started. Job ID: {query_job.job_id}")

    start_time = time.time()
    while time.time() - start_time < timeout:
        if query_job.done():
            if query_job.error_result:
                raise BadRequest(query_job.error_result)
            return query_job.state
        else:
            print("Query still running...")
            time.sleep(10)
            query_job.reload()
    return query_job.job_id

def transform_string(text):
    temp_text = re.sub(r"[^\w\s-]", " ", text)
    temp_text = re.sub(r"\s+", "_", temp_text)
    transformed_text = temp_text.strip("_-")
    return transformed_text