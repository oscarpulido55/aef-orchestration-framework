import datetime
import threading
from time import sleep

from google.api_core.client_options import ClientOptions
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

db = firestore.Client(project="dp-111-trf")
# [START firestore_data_set_from_map_nested]
data = {
    "workflows_name": "workflow1",
    "crond_expression": "0 7 * * ? *",
    "date_format": "%Y-%m-%d",
    "workflow_status": "ENABLED",
    "workflow_properties": {
        "database_project_name":"dev111"
    }
}
db.collection("workflows_scheduling").document("workflow1").set(data)

users_ref = db.collection("workflows_scheduling")
docs = users_ref.stream()

for doc in docs:
    print(f"{doc.id} => {doc.to_dict()}")