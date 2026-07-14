terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ── BigQuery Scheduled Query (Transfer Config) ────────────────────────────────

resource "google_bigquery_data_transfer_config" "dataform_failure_checker" {
  project                = var.project_id
  location               = var.bq_location
  display_name           = "Dataform Job Failure Checker"
  data_source_id         = "scheduled_query"
  schedule               = "every day 13:15"   # 13:15 UTC = 7:15 AM CT
  destination_dataset_id = var.target_dataset

  params = {
    query                          = local.failure_query
    destination_table_name_template = "recent_failures"
    write_disposition              = "WRITE_TRUNCATE"
  }

  # Ensures the target dataset exists before creating the transfer config
  depends_on = [google_bigquery_dataset.error_logs]
}

# ── Target Dataset (idempotent — won't recreate if it already exists) ─────────

resource "google_bigquery_dataset" "error_logs" {
  project                     = var.project_id
  dataset_id                  = var.target_dataset
  location                    = var.bq_location
  description                 = "Dataform pipeline error logs"
  delete_contents_on_destroy  = false   # safety: never drop tables on terraform destroy
}

# ── Query (local to keep params block readable) ───────────────────────────────

locals {
  failure_query = <<-SQL
    SELECT
      job_id,
      creation_time,
      error_result.reason  AS reason,
      error_result.message AS message
    FROM `${var.project_id}`.`region-${lower(var.bq_location)}`.INFORMATION_SCHEMA.JOBS
    WHERE
      creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 60 MINUTE)
      AND user_email   = '${var.dataform_service_account}'
      AND error_result IS NOT NULL
      AND state        = 'DONE'
  SQL
}

