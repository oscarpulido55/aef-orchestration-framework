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
import os
from google.cloud import dataform_v1beta1


# --- Dataform Client ---
df_client = dataform_v1beta1.DataformClient()
# --- Authentication Setup ---
credentials, project = google.auth.default()


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
        dataform_location = request_json.get('workflow_properties').get('dataform_location', None)
        dataform_project_id = request_json.get('workflow_properties').get('dataform_project_id', None)
        repository_name = request_json.get('workflow_properties').get('repository_name', None)
        tags = request_json.get('workflow_properties').get('tags', None)
        branch = request_json.get('workflow_properties').get('branch', None)

        workflow_name = request_json.get('workflow_name', None)
        job_name = request_json.get('job_name', None)
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


def run_repo_or_get_status(job_id: str, gcp_project: str, location: str, repo_name: str, tags: list, branch: str,
                           query_variables: dict):
    if job_id:
        return get_workflow_state(job_id)
    else:
        return run_workflow(gcp_project, location, repo_name, tags, True, branch)


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


def compile_workflow(repo_uri: str, branch: str):
    """Compiles a Dataform workflow using a specified Git branch.

    Args:
        repo_uri (str): The URI of the Dataform repository.
        gcp_project (str): The GCP project ID.
        tag (str): The dataform tag to compile.
        branch (str): The Git branch to compile.

    Returns:
        str: The name of the created compilation result.
    """
    request = dataform_v1beta1.CreateCompilationResultRequest(
        parent=repo_uri,
        compilation_result=dataform_v1beta1.types.CompilationResult(
            git_commitish=branch
        )
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


def run_workflow(gcp_project: str, location: str, repo_name: str, tags: list, execute: str, branch: str):
    """Orchestrates the complete Dataform workflow process: compilation and execution.

    Args:
        gcp_project (str): The GCP project ID.
        location (str): The GCP region.
        repo_name (str): The name of the Dataform repository.
        tags (str): The target tags to compile and execute.
        branch (str): The Git branch to use.
    """
    repo_uri = f'projects/{gcp_project}/locations/{location}/repositories/{repo_name}'
    compilation_result = compile_workflow(repo_uri, branch)
    if execute:
        workflow_invocation_name = execute_workflow(repo_uri, compilation_result, tags)
        return f"aef-{workflow_invocation_name}"
