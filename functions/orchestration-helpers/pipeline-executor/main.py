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
from datetime import date, timedelta, datetime
import json
import logging
import functions_framework
import google.oauth2.id_token
from google.cloud import error_reporting
from google.cloud import workflows_v1
from google.cloud.workflows import executions_v1
from google.cloud.workflows.executions_v1.types.executions import Execution

# Access environment variables
WORKFLOW_CONTROL_PROJECT_ID = os.environ.get('WORKFLOW_CONTROL_PROJECT_ID')
WORKFLOW_CONTROL_DATASET_ID = os.environ.get('WORKFLOW_CONTROL_DATASET_ID')
WORKFLOW_CONTROL_TABLE_ID = os.environ.get('WORKFLOW_CONTROL_TABLE_ID')
WORKFLOWS_LOCATION = os.environ.get('WORKFLOWS_LOCATION')
DEFAULT_TIME_FORMAT = '%Y-%m-%d'

# Logs
error_client = error_reporting.Client()
client = google.cloud.logging.Client()
client.setup_logging()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# clients
bq_client = bigquery.Client(project=WORKFLOW_CONTROL_PROJECT_ID)
execution_client = executions_v1.ExecutionsClient()
workflows_client = workflows_v1.WorkflowsClient()


@functions_framework.http
def main(request):
    """
    Main function, likely triggered by an HTTP request
    its main responsibility is to trigger a cloud workflows pipeline, parsing start and end
    execution dates, and logging to bigquery control table.

    Args:
        request: The incoming HTTP request object.

    """
    event = request.get_json()
    print("event: " + str(event))
    start_date = event.get('start_date')
    end_date = event.get('end_date')
    workflows_name = event.get('workflows_name')
    validation_date_pattern = event.get('validation_date_pattern')
    same_day_execution = event.get('same_day_execution', 'YESTERDAY')
    workflow_status = event.get('workflow_status')
    workflow_properties = event.get('workflow_properties')
    execution_id = 0
    try:
        if workflow_status == "ENABLED":
            execution_id = call_workflows(workflows_name, start_date, end_date,
                                          validation_date_pattern, workflow_properties,
                                          same_day_execution)
            log_step_bigquery(execution_id, event)
        else:
            print('Workflow Disabled')
        return execution_id
    except Exception as ex:
        exception_message = "Exception : " + repr(ex)
        error_client.report_exception()
        logger.error(exception_message)
        print(RuntimeError(repr(ex)))
        return exception_message, 500


def call_workflows(workflows_name, start_date, end_date,
                   validation_date_pattern, workflow_properties,
                   same_day_execution):
    """
    calls a cloud workflows pipeline passed by parameter

    Args:
        workflows_name: name of te cloud workflows to execute
        start_date: start date passed by parameter to the workflows pipeline ( normally a data pipeline )
        end_date: end date passed by parameter to the workflows pipeline ( normally a data pipeline )
        validation_date_pattern: python data pattern format to apply to start and end dates
        workflow_properties: custom properties passed to the cloud workflows.
        same_day_execution: can be YESTERDAY, TODAY or YESTERDAY_TODAY indicating dates that should be passed in
        start and end dates, if not received by parameter.

    Returns:
        execution_id: cloud workflows unique execution identifier
    """
    print("Launching Custom Workflow.....")

    if start_date is None:  # it means is not done manually
        start_date, end_date = process_dates(validation_date_pattern, same_day_execution)
    if end_date is None:
        end_date = start_date
    if isinstance(workflow_properties, str):
        workflow_properties = json.loads(workflow_properties)
    arguments = {
        "workflow_name": workflows_name,
        "query_variables": {
            "start_date": start_date,
            "end_date": end_date,
        },
        "workflow_properties": workflow_properties
    }
    print('Cloud Workflows input params: %s ', arguments)
    execution = Execution(argument=json.dumps(arguments))
    # Construct the fully qualified location path.
    parent = workflows_client.workflow_path(WORKFLOW_CONTROL_PROJECT_ID, WORKFLOWS_LOCATION, workflows_name)

    # Execute the workflow.
    response = execution_client.create_execution(parent=parent, execution=execution)
    execution_id = response.name.split("/")[-1]
    print(f"Created execution: {execution_id}")
    return execution_id


def process_dates(validation_date_pattern, same_day_execution):
    """method to process start and end dates when no received by parameter

    Args:
        validation_date_pattern: python data pattern format to apply to start and end dates
        same_day_execution: can be YESTERDAY, TODAY or YESTERDAY_TODAY indicating dates that should be passed in
        start and end dates, if not received by parameter.

    Returns:
        Start and end dates parsed

    """
    today = date.today()
    # if is a daily pattern, execute the previous day
    if validation_date_pattern == DEFAULT_TIME_FORMAT:
        if same_day_execution == 'YESTERDAY':
            last_day = today - timedelta(days=1)
        else:  # TODAY, YESTERDAY_TODAY
            last_day = today
        end_date = str(last_day.strftime(validation_date_pattern))
        if same_day_execution == 'TODAY':
            start_date = today
        else:  # YESTERDAY_TODAY, YESTERDAY
            start_date = today - timedelta(days=1)
        start_date = str(start_date.strftime(validation_date_pattern))
    # is a monthly pattern, execute the pattern the last month with regard
    # to the actual date
    else:
        first = today.replace(day=1)
        last_month_last_day = first - timedelta(days=1)
        last_month_first_day = last_month_last_day.replace(day=1)
        end_date = str(last_month_last_day.strftime(validation_date_pattern))
        start_date = str(last_month_first_day.strftime(validation_date_pattern))
    return start_date, end_date


# TODO complete log step
def log_step_bigquery(execution_id, event):
    """
    Logs a new entry in workflows bigquery table

    Args:
        execution_id: id of the execution
        event: event object containing info to log

    """
    current_datetime = datetime.now().isoformat()
    data = {
        'workflow_execution_id': execution_id,
        'workflow_name': event['workflows_name'],
        'job_name': "START_PIPELINE",
        'job_status': 'SUCCESS',
        'start_date': current_datetime,
        'end_date': current_datetime,
        'error_code': '0',
        'job_params': str(event),
        'log_path': '',
        'retry_count': 0,
        'execution_time_seconds': 0,
        'message': ''
    }
    workflows_control_table = bq_client.dataset(WORKFLOW_CONTROL_DATASET_ID).table(WORKFLOW_CONTROL_TABLE_ID)
    errors = bq_client.insert_rows_json(workflows_control_table, [data])  # Use list for multiple inserts
    if not errors:
        print("New row has been added.")
    else:
        raise Exception("Encountered errors while inserting row: {}".format(errors))
