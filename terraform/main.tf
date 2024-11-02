/*
Terraform configuration for setting up Google Cloud Pub/Sub infrastructure
for the data processing service.

Resources created:
1. Google Pub/Sub topic for message queueing.
2. Google Pub/Sub subscription to invoke the consumer service.
*/

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

resource "google_pubsub_topic" "data_topic" {
  name = var.pubsub_topic
}

resource "google_pubsub_subscription" "data_subscription" {
  name  = "data-subscription"
  topic = google_pubsub_topic.data_topic.name

  push_config {
    push_endpoint = "YOUR-CONSUMER-ENDPOINT"
  }
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
