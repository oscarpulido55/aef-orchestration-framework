#!/bin/bash
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#   Required Google Cloud APIs:
#   - BigQuery Connection API
#   - BigQuery Data Policy API
#   - Dataform API
#   - Error Reporting API
#   - —
#  - Compute Engine API
#   - Service Networking API
#   - —
#   - Secret Manager API
#   - —
#   - Google Cloud Firestore API
#   - Cloud Functions API
#   - Cloud Run Admin API
#   - Cloud Build API
#   - Eventarc API
#   - Workflows API
#   - —
#   - Cloud Scheduler API
#   - Dataflow API
#   - Error Reporting API
#   - Cloud Dataproc API
#   - Cloud Composer
#   - Cloud Data Lineage

gcloud config set project $1
gcloud services enable bigquery.googleapis.com \
                       bigquerydatapolicy.googleapis.com \
                       bigqueryconnection.googleapis.com \
                       cloudbuild.googleapis.com \
                       storage-component.googleapis.com \
                       cloudresourcemanager.googleapis.com \
                       dataflow.googleapis.com \
                       dataform.googleapis.com \
                       clouderrorreporting.googleapis.com \
                       compute.googleapis.com \
                       servicenetworking.googleapis.com \
                       secretmanager.googleapis.com \
                       firestore.googleapis.com \
                       cloudfunctions.googleapis.com \
                       run.googleapis.com \
                       eventarc.googleapis.com \
                       workflows.googleapis.com \
                       cloudscheduler.googleapis.com \
                       datacatalog.googleapis.com

gcloud services enable bigquery.googleapis.com \
                       dataproc.googleapis.com \
                       composer.googleapis.com \
                       datalineage.googleapis.com \
                       clouderrorreporting.googleapis.com