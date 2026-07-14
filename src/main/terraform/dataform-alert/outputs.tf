output "transfer_config_id" {
  description = "Resource name of the BQ scheduled query transfer config"
  value       = google_bigquery_data_transfer_config.dataform_failure_checker.id
}

output "transfer_config_name" {
  description = "Full resource name — use this with bq show --transfer_config"
  value       = google_bigquery_data_transfer_config.dataform_failure_checker.name
}

output "target_table" {
  description = "Fully qualified table where failures are written"
  value       = "${var.project_id}.${var.target_dataset}.recent_failures"
}

output "next_run_time" {
  description = "When the scheduled query will next run"
  value       = google_bigquery_data_transfer_config.dataform_failure_checker.next_run_time
}
