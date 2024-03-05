import google.auth
import functions_framework
import grpc
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
    """
    Main function, likely triggered by an HTTP request. Extracts parameters, reads a file from
    Dataform, executes the file's contents as a BigQuery query, and reports the result status or job ID.

    Args:
        request: The incoming HTTP request object.

    Returns:
        str: The status of the query execution or the job ID (if asynchronous).
    """

    request_json = request.get_json(silent=True)

    location = request_json['location']
    dataform_project_id = request_json['dataform_project_id']
    repository_name = request_json['repository_name']
    file_path = request_json['file_path']
    bq_project_id = request_json['bq_project_id']
    job_id = request_json.get('job_id', None)
    query_variables = request_json.get('query_variables', None)

    query_file = read_file(dataform_project_id, location, repository_name, file_path, query_variables)
    status_or_job_id = execute_query_or_get_status(bq_project_id, query_file, file_path, job_id)

    if status_or_job_id.startswith('aef_'):
        print(f"Running Query, track it with Job ID: {status_or_job_id}")
    else:
        print(f"Query finished with status: {status_or_job_id}")

    return status_or_job_id


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
        return file_contents
    else:
        print("API request failed. Status code:", response.status_code)
        print(response.text)
        return None


def read_file_grpc(project_id, location, repository_name, file_path, commit_sha=None):
    """Reads a file from a Dataform repository using gRPC method.
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
        query_job = client.query(query_file, job_id=job_id)
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