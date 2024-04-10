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
import json
import logging
import google.cloud.logging
import functions_framework
import google.oauth2.id_token
from google.cloud import error_reporting
from cloudevents.http import CloudEvent
from google.cloud import firestore
from google.events.cloud import firestore as firestoredata
from google.cloud import scheduler_v1


# Access environment variables
WORKFLOW_SCHEDULING_PROJECT_ID = os.environ.get('WORKFLOW_SCHEDULING_PROJECT_ID')
WORKFLOW_SCHEDULING_PROJECT_NUMBER = os.environ.get('WORKFLOW_SCHEDULING_PROJECT_NUMBER')
WORKFLOW_SCHEDULING_PROJECT_REGION = os.environ.get('WORKFLOW_SCHEDULING_PROJECT_REGION')
WORKFLOW_SCHEDULING_FIRESTORE_COLLECTION = os.environ.get('WORKFLOW_SCHEDULING_FIRESTORE_COLLECTION')
PIPELINE_EXECUTION_FUNCTION_NAME = os.environ.get('PIPELINE_EXECUTION_FUNCTION_NAME')

# define clients
error_client = error_reporting.Client()
client = google.cloud.logging.Client()
client.setup_logging()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
firestore_client = firestore.Client()
scheduler_client = scheduler_v1.CloudSchedulerClient()

@functions_framework.cloud_event
def main(cloud_event: CloudEvent) -> None:
    """
    Main function, likely triggered by an eventarc event coming from firestore.
    Acts as a lif cycle manager for cloud scheduling rules that triggers cloud workflows pipelines through
    pipeline executor function, creating, updating and deleting them when necessary.

    Args:
        request: The incoming eventarc request object.

    """
    print(f"EVENT::: path: {cloud_event}")
    firestore_payload = firestoredata.DocumentEventData()
    firestore_payload._pb.ParseFromString(cloud_event.data)

    document_value = None
    if firestore_payload.value:
        document_value = firestore_payload.value
    elif firestore_payload.old_value:
        document_value = firestore_payload.old_value
    path_parts = document_value.name.split("/")
    separator_idx = path_parts.index("documents")
    collection_path = path_parts[separator_idx + 1]
    document_path = "/".join(path_parts[(separator_idx + 2) :])
    job_name = document_path

    print(f"Collection path: {collection_path}")
    print(f"Document path: {document_path}")

    if determine_job_type(firestore_payload.old_value, firestore_payload.value) in ('CREATE','UPDATE'):
        crond_expression = firestore_payload.value.fields["crond_expression"].string_value
        validation_date_pattern = firestore_payload.value.fields["date_format"].string_value
        time_zone = firestore_payload.value.fields["time_zone"].string_value
        workflow_status = firestore_payload.value.fields["workflow_status"].string_value
        workflow_properties = firestore_payload.value.fields["workflow_properties"].string_value
        workflow_parameters = {
            "workflows_name" : job_name,
            "validation_date_pattern" : validation_date_pattern,
            "same_day_execution" : "YESTERDAY",
            "workflow_status" : workflow_status,
            "workflow_properties" : workflow_properties
        }
        if determine_job_type(firestore_payload.old_value, firestore_payload.value) == 'CREATE':
            create_job(job_name, crond_expression, time_zone, workflow_parameters)
        if determine_job_type(firestore_payload.old_value, firestore_payload.value) == 'UPDATE':
            update_job(job_name, crond_expression, time_zone, workflow_parameters)
    if determine_job_type(firestore_payload.old_value, firestore_payload.value) in ('CREATE','UPDATE'):
        change_status(job_name, firestore_payload.value)
    if determine_job_type(firestore_payload.old_value, firestore_payload.value) == 'DELETE':
        delete_job(job_name)


def determine_job_type(old_value ,new_value):
    """
    Evaluates what type of event was triggered in firestore: CREATE, UPDATE or DELETE

    Args:
        old value: old firestore value coming in trigger info
        new value:  new firestore value coming in trigger info

    Returns:
        type of event
    """
    if new_value and not old_value:
        return 'CREATE'
    elif old_value and not new_value:
        return 'DELETE'
    elif old_value and new_value:
        return 'UPDATE'



def create_job(job_name, crond_expression, time_zone, workflow_parameters):
    """
    creates a scheduler job , using given parameters.

    Args:
        job_name: name for the scheduler job, should be the same as cloud workflows name
        crond_expression:  crond linux expression used to trigger the cloud scheduler rule
        time_zone: timezone associated with scheduler execution.
        workflow_parameters: parameters sent to the cloud workflows invocation

    """
    parent= scheduler_client.common_location_path(WORKFLOW_SCHEDULING_PROJECT_ID,WORKFLOW_SCHEDULING_PROJECT_REGION)
    job={
        "name":"projects/"+ WORKFLOW_SCHEDULING_PROJECT_ID+ "/locations/"+WORKFLOW_SCHEDULING_PROJECT_REGION+"/jobs/" + job_name,
        "description":"workflows scheduler job create",
        "http_target": {
            "http_method": "POST",
            "uri": f"https://{WORKFLOW_SCHEDULING_PROJECT_REGION}-{WORKFLOW_SCHEDULING_PROJECT_ID}.cloudfunctions.net/{PIPELINE_EXECUTION_FUNCTION_NAME}" ,
            "headers": {"Content-Type": "application/json"},
            "oidc_token": {"service_account_email": WORKFLOW_SCHEDULING_PROJECT_NUMBER + "-compute@developer.gserviceaccount.com"},
            "body": json.dumps(workflow_parameters).encode("utf-8"),
        },
        "schedule":crond_expression,
        "time_zone":time_zone,
    }
    scheduler_client.create_job(parent=parent,job=job)
    print("JOB CREATED...........")


def update_job(job_name, crond_expression, time_zone, workflow_parameters):
    """
    updates a scheduler job , using given parameters.

    Args:
        job_name: name for the scheduler job, should be the same as cloud workflows name
        crond_expression:  crond linux expression used to trigger the cloud scheduler rule
        time_zone: timezone associated with scheduler execution.
        workflow_parameters: parameters sent to the cloud workflows invocation

    """
    job={
        "name":"projects/"+ WORKFLOW_SCHEDULING_PROJECT_ID+ "/locations/"+WORKFLOW_SCHEDULING_PROJECT_REGION+"/jobs/" + job_name,
        "description":"workflows scheduler job update",
        "http_target": {
            "http_method": "POST",
            "uri": f"https://{WORKFLOW_SCHEDULING_PROJECT_REGION}-{WORKFLOW_SCHEDULING_PROJECT_ID}.cloudfunctions.net/{PIPELINE_EXECUTION_FUNCTION_NAME}" ,
            "headers": {"Content-Type": "application/json"},
            "oidc_token": {"service_account_email": WORKFLOW_SCHEDULING_PROJECT_NUMBER + "-compute@developer.gserviceaccount.com"},
            "body": json.dumps(workflow_parameters).encode("utf-8"),
        },
        "schedule":crond_expression,
        "time_zone":time_zone,
    }
    scheduler_client.update_job(job=job)
    print("JOB UPDATED...........")


def delete_job(job_name):
    """
    deletes a scheduler job , using given parameters.

    Args:
        job_name: name for the scheduler job, should be the same as cloud workflows name

    """
    final_job_name = "projects/"+ WORKFLOW_SCHEDULING_PROJECT_ID+ "/locations/"+WORKFLOW_SCHEDULING_PROJECT_REGION+"/jobs/" + job_name
    scheduler_client.delete_job(name=final_job_name)
    print("JOB DELETED...........")


def change_status(job_name, new_value):
    """
    evaluates if a cloud scheduler rule must be paused or resumed, depending on firestore trigger

    Args:
        job_name: name for the scheduler job, should be the same as cloud workflows name
        new value:  new firestore value coming in trigger info

    """
    workflow_status = new_value.fields["workflow_status"].string_value
    print(f"workflow_status: {workflow_status} ")
    if workflow_status == 'DISABLED':
        pause_job(job_name)
    if workflow_status == 'ENABLED':
        resume_job(job_name)


def pause_job(job_name):
    """
    pauses a scheduler job , using given parameters.

    Args:
        job_name: name for the scheduler job, should be the same as cloud workflows name

    """
    final_job_name = "projects/"+ WORKFLOW_SCHEDULING_PROJECT_ID+ "/locations/"+WORKFLOW_SCHEDULING_PROJECT_REGION+"/jobs/" + job_name
    scheduler_client.pause_job(name=final_job_name)
    print("JOB PAUSED...........")

def resume_job(job_name):
    """
    resumes a scheduler job , using given parameters.

    Args:
        job_name: name for the scheduler job, should be the same as cloud workflows name

    """
    final_job_name = "projects/"+ WORKFLOW_SCHEDULING_PROJECT_ID+ "/locations/"+WORKFLOW_SCHEDULING_PROJECT_REGION+"/jobs/" + job_name
    scheduler_client.resume_job(name=final_job_name)
    print("JOB RESUMED...........")