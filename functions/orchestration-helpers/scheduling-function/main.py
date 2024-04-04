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
from datetime import datetime
import google.auth
import urllib
import urllib.error
import urllib.request
import json
import logging
import google.cloud.logging
import google.auth.transport.requests
import functions_framework
import google.oauth2.id_token
from google.cloud import error_reporting
from cloudevents.http import CloudEvent
from google.cloud import firestore
from google.events.cloud import firestore as firestoredata
from google.cloud import scheduler_v1


# Access environment variables
#WORKFLOW_SCHEDULING_PROJECT_ID = os.environ.get('WORKFLOW_CONTROL_PROJECT_ID')

# define clients
error_client = error_reporting.Client()
client = google.cloud.logging.Client()
client.setup_logging()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
firestore_client = firestore.Client()
scheduler_client = scheduler_v1.CloudSchedulerClient()

PROJECT_ID = "dp-111-trf"
LOCATION_ID ='us-central1'

@functions_framework.cloud_event
def main(cloud_event: CloudEvent) -> None:
    print(f"EVENT::: path: {cloud_event}")
    firestore_payload = firestoredata.DocumentEventData()
    firestore_payload._pb.ParseFromString(cloud_event.data)

    path_parts = firestore_payload.value.name.split("/")
    separator_idx = path_parts.index("documents")
    collection_path = path_parts[separator_idx + 1]
    document_path = "/".join(path_parts[(separator_idx + 2) :])

    print(f"Collection path: {collection_path}")
    print(f"Document path: {document_path}")

    print(f"Function triggered by change to: {cloud_event['source']}")

    #print("\nOld value:")
    #print(firestore_payload.old_value)

    #print("\nNew value:")
    #print(firestore_payload.value)

    affected_doc = firestore_client.collection(collection_path).document(document_path)
    create_job(document_path)
    cur_value = firestore_payload.value.fields["workflow_status"].string_value
    print(f"workflow_status: {cur_value} ")


def create_job(job_name):
    body = {"Hello": "World"}
    parent= scheduler_client.common_location_path(PROJECT_ID,LOCATION_ID)
    job={
        "name":"projects/"+ PROJECT_ID+ "/locations/"+LOCATION_ID+"/jobs/" + job_name,
        "description":"this is for testing ",
        "http_target": {
            "http_method": "POST",
            "uri": "https://us-central1-dp-111-trf.cloudfunctions.net/orch-framework-intermediate-function",
            "headers": {"Content-Type": "application/json"},
            "oidc_token": {"service_account_email": "713778431230-compute@developer.gserviceaccount.com"},
            "body": json.dumps(body).encode("utf-8"),
        },
        "schedule":"0 7 * * *",
        "time_zone":"America/Los_Angeles",
    }
    scheduler_client.create_job(parent=parent,job=job)
    print("JOB CREATED...........")
