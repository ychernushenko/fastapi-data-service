terraform {
  backend "gcs" {
    bucket = "fastapi-data-service"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_sql_database_instance" "postgres_instance" {
  name             = "fastapi-postgres"
  database_version = "POSTGRES_13"
  region           = var.region
  settings {
    tier = "db-g1-small"
  }
}

resource "google_sql_database" "app_database" {
  name     = "appdb"
  instance = google_sql_database_instance.postgres_instance.name
}

resource "google_cloud_run_service" "fastapi_service" {
  name     = "fastapi-service"
  location = var.region
  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/fastapi-service:latest"
      }
    }
  }
  autogenerate_revision_name = true
}

# IAM Binding for unauthenticated access to Cloud Run
resource "google_cloud_run_service_iam_binding" "allow_unauthenticated" {
  location = var.region
  project  = var.project_id
  service  = google_cloud_run_service.fastapi_service.name
  role     = "roles/run.invoker"
  members  = ["allUsers"]
}
