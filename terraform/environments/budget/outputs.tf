output "cloud_run_url" {
  description = "The public URL of the Cloud Run orchestrator Fast API."
  value       = google_cloud_run_v2_service.orchestrator_api.uri
}

output "storage_bucket_name" {
  description = "The name of the GCS bucket for PDF uploads."
  value       = google_storage_bucket.permit_uploads.name
}

output "service_account_email" {
  description = "The Service Account email used by the back-end to generate Pre-signed URLs."
  value       = google_service_account.orchestrator_sa.email
}
