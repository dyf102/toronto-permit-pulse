# ------------------------------------------------------------------------------
# Input Variables
# ------------------------------------------------------------------------------

variable "gcp_project_id" {
  description = "The ID of the GCP project where resources will be mapped."
  type        = string
  default     = "crossbeam-toronto"
}

variable "gcp_region" {
  description = "GCP Region for Cloud Run compute"
  type        = string
  default     = "us-east4" # Using Northern Virginia for proximity to Toronto / Free tier compatibility
}
