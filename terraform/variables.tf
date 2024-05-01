/**
 * Copyright 2024 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

variable "project" {
  description = "Project ID where the AEF Orchestration Framework will be deployed."
  type        = string
  nullable    = false
}

variable "region" {
  description = "Name of the region for the components to be deployed"
  type        = string
  nullable    = false
}

variable "operator_email" {
  description = "email of the data platform operator for error notifications"
  type        = string
  nullable    = false
}

variable "workflows_scheduling_table_name" {
  description = "workflows scheduling table name"
  type        = string
  nullable    = false
  default     = "workflows_scheduling"
}

