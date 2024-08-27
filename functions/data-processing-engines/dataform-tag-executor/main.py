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
import logging
import functions_framework
from google.cloud import dataform_v1beta1
from google.cloud import secretmanager_v1
from google.cloud import storage
import requests
import json
import os

# --- Dataform Client ---
df_client = dataform_v1beta1.DataformClient()
# --- Authentication Setup ---
credentials, project = google.auth.default()
# --- GCS Client ---
storage_client = storage.Client()
function_name = os.environ.get('K_SERVICE')

@functions_framework.http
def main(request):
    """
    Main function, likely triggered by an HTTP request. Extracts parameters, reads a repository from
    Dataform, executes the file's contents as a BigQuery query, and reports the result status or job ID.

    Args:
        request: The incoming HTTP request object.

    Returns:
        str: The status of the query execution or the job ID (if asynchronous).
    """

    request_json = request.get_json(silent=True)
    print("event:" + str(request_json))

    try:
        job_name = request_json.get('job_name', None)
        workflow_name = request_json.get('workflow_name', None)

        jobs_definitions_bucket = request_json.get("workflow_properties", {}).get("jobs_definitions_bucket")
        repository_name = None
        tags = None
        branch = None
        dataform_location = None
        dataform_project_id = None

        if jobs_definitions_bucket:
            extracted_params = extract_params(
                bucket_name=jobs_definitions_bucket,
                job_name=job_name,
                function_name=function_name
            )
            repository_name = extracted_params.get("repository_name")
            tags = extracted_params.get("tags")
            branch = extracted_params.get("branch")
            dataform_location = extracted_params.get("dataform_location")
            dataform_project_id = extracted_params.get("dataform_project_id")

        job_id = request_json.get('job_id', None)
        query_variables = request_json.get('query_variables', None)

        status_or_job_id = run_repo_or_get_status(job_id, gcp_project=dataform_project_id, location=dataform_location,
                                                  repo_name=repository_name, tags=tags, branch=branch,
                                                  query_variables=query_variables)

        if status_or_job_id.startswith('aef_'):
            print(f"Running Query, track it with Job ID: {status_or_job_id}")
        else:
            print(f"Query finished with status: {status_or_job_id}")

        return status_or_job_id
    except Exception as error:
        err_message = "Exception: " + repr(error)
        response = {
            "error": error.__class__.__name__,
            "message": repr(err_message)
        }
        return response

def extract_params(bucket_name, job_name, function_name, encoding='utf-8'):
    """Extracts parameters from a JSON file.

    Args:
        bucket_name: Bucket containing the JSON parameters file .

    Returns:
        A dictionary containing the extracted parameters.
    """

    json_file_path = f'gs://{bucket_name}/{function_name}/{job_name}.json'

    parts = json_file_path.replace("gs://", "").split("/")
    bucket_name = parts[0]
    object_name = "/".join(parts[1:])
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(object_name)

    try:
        json_data = blob.download_as_bytes()
        params = json.loads(json_data.decode(encoding))
        return params
    except (google.cloud.exceptions.NotFound, json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error reading JSON file: {e}")
        return None


def run_repo_or_get_status(job_id: str, gcp_project: str, location: str, repo_name: str, tags: list, branch: str,
                           query_variables: dict):
    if job_id:
        return get_workflow_state(job_id)
    else:
        return run_workflow(gcp_project, location, repo_name, tags, True, branch, query_variables)


def execute_workflow(repo_uri: str, compilation_result: str, tags: list):
    """Triggers a Dataform workflow execution based on a provided compilation result.

    Args:
        repo_uri (str): The URI of the Dataform repository.
        compilation_result (str): The name of the compilation result to use.

    Returns:
        str: The name of the created workflow invocation.
    """
    invocation_config = dataform_v1beta1.types.InvocationConfig(
        included_tags=tags
    )
    request = dataform_v1beta1.CreateWorkflowInvocationRequest(
        parent=repo_uri,
        workflow_invocation=dataform_v1beta1.types.WorkflowInvocation(
            compilation_result=compilation_result,
            invocation_config=invocation_config
        )
    )
    response = df_client.create_workflow_invocation(request=request)
    name = response.name
    logging.info(f'created workflow invocation {name}')
    return name


def access_secret_version(project_id: str, secret_id: str, version_id: str = "1") -> str:
    """
    Accesses the value of the specified Secret Version.
    """

    client = secretmanager_v1.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


def get_dataform_json_from_github(repo_url, github_token, branch="main", path="dataform.json"):
    """Fetches dataform.json from a GitHub repository."""
    url = f"{repo_url}/raw/{branch}/{path}"
    headers = {"Authorization": f"token {github_token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def merge_compilation_config(
        compilation_config: dataform_v1beta1.types.CodeCompilationConfig,
        query_variables: dict,
        dataform_json_content: dict
):
    """Merges Dataform repository default compilation settings with input query variables.

    This function reads the `dataform.json` file from the Dataform repository,
    merges its contents with the provided `query_variables`, and updates the
    given `compilation_config` with the merged result.

    Variables defined in `query_variables` will take precedence over variables
    defined in `dataform.json`. Variables present in `dataform.json` but not
    in `query_variables` will be retained in the merged configuration.

    Args:
        compilation_config: The
            google.cloud.dataform_v1beta1.types.CodeCompilationConfig object
            to update with the merged configuration.
        query_variables: A dictionary containing query variables and their values.
        dataform_json_content: A dictionary containing the content of dataform.json.

    Returns:
        None. The `compilation_config` object is updated in-place.
    """

    # Get the 'vars' section from dataform.json
    dataform_vars = dataform_json_content.get("vars", {})

    # Merge query_variables with dataform_vars, with query_variables taking precedence
    merged_vars = {**dataform_vars, **query_variables}

    # Update the vars field in the compilation_config
    compilation_config.vars.update(merged_vars)


def compile_workflow(gcp_project: str, repo_name: str, repo_uri: str, branch: str, query_variables: dict):
    """Compiles a Dataform workflow using a specified Git branch.

    Returns:
        str: The name of the created compilation result.
    """

    github_token = access_secret_version(gcp_project, repo_name + "_secret")

    dataform_json_content = get_dataform_json_from_github(
        df_client
            .get_repository(name=repo_uri)
            .git_remote_settings.url
            .replace(".git", ""),
        github_token)

    compilation_result = dataform_v1beta1.CompilationResult(
        git_commitish=branch,
    )

    merge_compilation_config(compilation_result.code_compilation_config, query_variables, dataform_json_content)

    print("compilation_result.code_compilation_config.vars::::::   " + str(
        compilation_result.code_compilation_config.vars))

    request = dataform_v1beta1.CreateCompilationResultRequest(
        parent=repo_uri,
        compilation_result=compilation_result
    )

    response = df_client.create_compilation_result(request=request)
    name = response.name
    logging.info(f'compiled workflow {name}')
    return name


def get_workflow_state(job_id: str):
    """Monitors the status of a Dataform workflow invocation.

    Args:
        job_id (str): The ID of the workflow invocation.
    """
    workflow_invocation_id = job_id.split("aef-", 1)[1]
    request = dataform_v1beta1.GetWorkflowInvocationRequest(
        name=workflow_invocation_id
    )
    response = df_client.get_workflow_invocation(request)
    state = response.state.name
    logging.info(f'workflow state: {state}')
    return state


def run_workflow(gcp_project: str, location: str, repo_name: str, tags: list, execute: str, branch: str,
                 query_variables: dict):
    """Orchestrates the complete Dataform workflow process: compilation and execution.

    Args:
        gcp_project (str): The GCP project ID.
        location (str): The GCP region.
        repo_name (str): The name of the Dataform repository.
        tags (str): The target tags to compile and execute.
        branch (str): The Git branch to use.
        query_variables (dict): Step specific variables like end or start date i.e. {'${start_date}': "'2024-05-21'", '${end_date}': "'2024-05-21'"}
    """
    repo_uri = f'projects/{gcp_project}/locations/{location}/repositories/{repo_name}'
    compilation_result = compile_workflow(gcp_project, repo_name, repo_uri, branch, query_variables)
    if execute:
        workflow_invocation_name = execute_workflow(repo_uri, compilation_result, tags)
        return f"aef-{workflow_invocation_name}"
