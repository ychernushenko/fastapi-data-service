variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "pubsub_topic" {
  description = "Google Cloud Pub/Sub topic name"
  default     = "data-topic"
}

variable "region" {
  description = "Google Cloud region"
  type        = string
  default     = "us-central1"
}

# Database credentials

variable "db_user" {
  description = "PostgreSQL database username"
  type        = string
}

variable "db_password" {
  description = "PostgreSQL database password"
  type        = string
}
