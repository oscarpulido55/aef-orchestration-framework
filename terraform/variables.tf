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
  description = "Project where the AEF Orchestration Framework will be deployed."
  type        = string
  nullable    = false
}

variable "region" {
  description = "Name of the bucket that will be used for the functions code. It will be created with prefix prepended if bucket_config is not null."
  type        = string
  nullable    = false
}

variable "dataform_project" {
  description = "Project where the dataform repositories reside."
  type        = string
  nullable    = false
}

variable "dataform_location" {
  description = "Location of the dataform project repository"
  type        = string
  nullable    = false
}

variable "dataform_repository" {
  description = "Name of the dataform repository"
  type        = string
  nullable    = false
}