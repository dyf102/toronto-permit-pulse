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
  project = var.gcp_project_id
  region  = var.gcp_region
}

# ------------------------------------------------------------------------------
# API & Cloud Run (Scale-to-Zero Budget Compute)
# ------------------------------------------------------------------------------
resource "google_cloud_run_v2_service" "orchestrator_api" {
  name     = "permit-pulse-orchestrator"
  location = var.gcp_region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello" # Placeholder until CI/CD pushes real image
      
      env {
        name  = "ENVIRONMENT"
        value = "budget-starter"
      }
      env {
        name  = "CORS_ORIGIN"
        value = "https://permit-pulse.ca"
      }
      
      resources {
        # Minimal resources for MVP orchestration
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }
    scaling {
      min_instance_count = 0 # True Serverless / Scale-to-zero for MVP
      max_instance_count = 2 # Hard cap to prevent runaway bills
    }
  }
}

# Allow public unauthenticated access to the Cloud Run service (API Gateway handles auth internally)
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  name     = google_cloud_run_v2_service.orchestrator_api.name
  location = google_cloud_run_v2_service.orchestrator_api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ------------------------------------------------------------------------------
# Object Storage (GCS bucket for Free Tier 250MB Uploads)
# ------------------------------------------------------------------------------
resource "google_storage_bucket" "permit_uploads" {
  name          = "${var.gcp_project_id}-permit-uploads"
  location      = "US" # Multi-region US is generally included in free tier/cheap
  force_destroy = false
  
  uniform_bucket_level_access = true

  # 90-day retention policy to comply with City PII data limits and save costs
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  # CORS configuration so the Next.js frontend can upload directly via Pre-signed URLs
  cors {
    origin          = ["http://localhost:3000", "https://permit-pulse.ca"]
    method          = ["GET", "PUT", "POST", "OPTIONS"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
}

# Service account for Cloud Run to access the GCS bucket to generate pre-signed URLs
resource "google_service_account" "orchestrator_sa" {
  account_id   = "permit-pulse-orchestrator-sa"
  display_name = "Orchestrator Service Account"
}

resource "google_storage_bucket_iam_member" "orchestrator_storage_admin" {
  bucket = google_storage_bucket.permit_uploads.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

# Update Cloud Run to use this SA
# Note: In a real deploy, the Cloud Run resource would reference `service_account = google_service_account.orchestrator_sa.email`
