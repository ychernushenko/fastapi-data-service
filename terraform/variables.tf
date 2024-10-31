variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud region"
  type        = string
  default     = "us-central1"
}

variable "credentials_file" {
  description = "Path to the Google Cloud credentials file"
  type        = string
}
