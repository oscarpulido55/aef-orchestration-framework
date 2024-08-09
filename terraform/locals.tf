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

locals {
  workflows_control = jsonencode([
    { name = "workflow_execution_id", type = "STRING" },
    { name = "workflow_name", type = "STRING" },
    { name = "job_name", type = "STRING" },
    { name = "job_status", type = "STRING" },
    { name = "timestamp", type = "DATETIME" },
    { name = "error_code", type = "STRING" },
    { name = "job_params", type = "STRING" },
    { name = "log_path", type = "STRING" },
    { name = "retry_count", type = "INTEGER" }
  ])
}
