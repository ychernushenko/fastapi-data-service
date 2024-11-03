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

# Google Pub/Sub Topic
resource "google_pubsub_topic" "data_topic" {
  name    = "data-topic"
  project = var.project_id
}

# Google Pub/Sub Subscription
resource "google_pubsub_subscription" "data_subscription" {
  name    = "data-subscription"
  topic   = google_pubsub_topic.data_topic.name
  project = var.project_id

  message_retention_duration = "604800s" # 7 days
}

# Cloud Run Service for FastAPI
resource "google_cloud_run_service" "fastapi_service" {
  name     = "fastapi-service"
  location = var.region
  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/fastapi-service:latest"
        env {
          name  = "DB_USER"
          value = var.db_user
        }
        env {
          name  = "DB_PASSWORD"
          value = var.db_password
        }
        env {
          name  = "DB_HOST"
          value = google_sql_database_instance.postgres_instance.connection_name
        }
        env {
          name  = "DB_NAME"
          value = google_sql_database.app_database.name
        }
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
      }
    }
  }
  autogenerate_revision_name = true
}

resource "google_cloud_run_service_iam_member" "fastapi_invoker" {
  project  = var.project_id
  location = var.region
  service  = google_cloud_run_service.fastapi_service.name
  role     = "roles/run.invoker"
  member   = "user:y.chernushenko@gmail.com"
}

# Google Cloud Function for Consumer
resource "google_cloudfunctions_function" "consumer_function" {
  name                  = "consumer-function-v3"
  runtime               = "python310"
  entry_point           = "pubsub_consumer"
  region                = var.region
  source_archive_bucket = "fastapi-data-service"
  source_archive_object = "functions-source/consumer-function.zip"

  environment_variables = {
    DB_USER     = var.db_user
    DB_PASSWORD = var.db_password
    DB_HOST     = google_sql_database_instance.postgres_instance.connection_name
    DB_NAME     = google_sql_database.app_database.name
    PROJECT_ID  = var.project_id
  }

  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = google_pubsub_topic.data_topic.name
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Cloud SQL PostgreSQL Instance
resource "google_sql_database_instance" "postgres_instance" {
  name             = "fastapi-postgres"
  database_version = "POSTGRES_13"
  region           = var.region
  settings {
    tier = "db-g1-small"
  }
  root_password = var.db_password
}

# Cloud SQL Database for the application
resource "google_sql_database" "app_database" {
  name     = "appdb"
  instance = google_sql_database_instance.postgres_instance.name
}

# Cloud SQL User
resource "google_sql_user" "db_user" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres_instance.name
  password = var.db_password
}
