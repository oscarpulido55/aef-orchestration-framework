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

resource "google_monitoring_notification_channel" "email-error-channel" {
  display_name = "Email Error Channel"
  type = "email"
  project = var.project
  labels = {
    email_address = var.operator_email
  }

}

resource "google_monitoring_alert_policy" "alert-intermediate-function" {
  display_name = "cloud functions async alert policy"
  project = var.project
  combiner     = "OR"
  conditions {
    display_name = "Error condition"
    condition_matched_log {
      filter = "(resource.type=\"cloud_run_revision\" resource.labels.service_name=\"${module.intermediate-function.function_name}\" resource.labels.location = \"${var.region}\" ) AND textPayload:Exception AND severity=\"ERROR\""
    }
  }

  notification_channels = [ google_monitoring_notification_channel.email-error-channel.name ]
  alert_strategy {
    notification_rate_limit {
      period = "300s"
    }
  }
}