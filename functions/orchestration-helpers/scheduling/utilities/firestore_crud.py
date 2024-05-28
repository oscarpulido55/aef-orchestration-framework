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


import argparse, logging

from google.cloud import firestore

WORKFLOWS_COLLECTION_DEFAULT_NAME = "workflows_scheduling"

def main(args, loglevel):
    logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)
    db = firestore.Client(project=args.gcp_project)
    if hasattr(args, 'workflow_properties'):
        print(args.workflow_properties)
        #workflow_props = json.loads(args.workflow_properties)
        workflow_props = args.workflow_properties
    if args.operation_type in('CREATE','UPDATE'):
        data = {
            "workflows_name": args.workflow_name,
            "crond_expression": args.crond_expression,
            "time_zone": args.time_zone,
            "date_format": args.date_format,
            "workflow_status": args.workflow_status,
            "workflow_properties": workflow_props
        }
        if args.operation_type == 'CREATE':
            create_doc(db, data)
        if args.operation_type == 'UPDATE':
            update_doc(db,data)
    if args.operation_type == 'DELETE':
        delete_doc(db)


def create_doc(db, data):
    db.collection(WORKFLOWS_COLLECTION_DEFAULT_NAME).document(args.workflow_name).set(data)
    print_documents(db)

def update_doc(db,data):
    db.collection(WORKFLOWS_COLLECTION_DEFAULT_NAME).document(args.workflow_name).update(data)
    print_documents(db)

def delete_doc(db):
    db.collection(WORKFLOWS_COLLECTION_DEFAULT_NAME).document(args.workflow_name).delete()
    print_documents(db)

def print_documents(db):
    doc_ref = db.collection(WORKFLOWS_COLLECTION_DEFAULT_NAME)
    docs = doc_ref.stream()
    for doc in docs:
        print(f"{doc.id} => {doc.to_dict()}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description = "Crud utility for firestore.",
        fromfile_prefix_chars = '@' )
    parser.add_argument("--operation_type",help="can be 'CREATE','UPDATE' or 'DELETE' ", required=True)
    parser.add_argument("--gcp_project",help="gco project containing the workflows_scheduling collection in firestore", required=True)
    parser.add_argument("--workflow_name",help="workflow name as named in cloud workflows service", required=True)
    args, unknown = parser.parse_known_args()
    if args.operation_type in ('CREATE','UPDATE'):
        parser.add_argument("--crond_expression",help="crond expression to schedlue the workflows. (eg. '0 7 * * *')", required=True)
        parser.add_argument("--time_zone",help="time zone associated with crond expression. (eg. 'America/Los_Angeles')", required=True)
        parser.add_argument("--date_format",help="python date format to be passed to the workflow execution (eg. '%Y-%m-%d')", required=True)
        parser.add_argument("--workflow_status",help="workflow status can be 'ENABLED' or 'DISABLED' to disable a workflow execution temporarily", required=True)
        parser.add_argument("--workflow_properties",help="properties to be passed as workflow input (eg. '{\"database_project_id\":\"prj-111\"}')", default='{}')

    parser.add_argument("-v","--verbose",help="increase output verbosity", action="store_true")
    args, unknown = parser.parse_known_args()

    # Setup logging
    if args.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    main(args, loglevel)



