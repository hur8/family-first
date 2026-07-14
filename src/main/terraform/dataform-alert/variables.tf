variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "father-first"
}

variable "region" {
  description = "GCP region for provider default"
  type        = string
  default     = "us-central1"
}

variable "bq_location" {
  description = "BigQuery dataset location"
  type        = string
  default     = "US"
}

variable "target_dataset" {
  description = "BigQuery dataset to write failure records into"
  type        = string
  default     = "error_logs"
}

variable "dataform_service_account" {
  description = "Service account email that runs Dataform jobs"
  type        = string
  default     = "ff-dataform-service-account@father-first.iam.gserviceaccount.com"
}
