provider "google" {
  credentials = file("C:\\development\\trellonotify-401705-34c3114d5a2c.json")
  project     = "trellonotify-401705"
  region      = "us-central1"
}

resource "google_storage_bucket" "function_source" {
  name     = "trellonotify-source-bucket"
  location = "us-central1"
}

resource "google_storage_bucket_object" "function_code" {
  name   = "${local.source_code_hash}.zip"
  bucket = google_storage_bucket.function_source.name
  source = "../build/code.zip" # assuming you've zipped your function and placed it in the build directory
}

locals {
  source_code_hash = substr(filesha256("../build/code.zip"), 0, 63)
}


resource "google_cloudfunctions_function" "test_function" {
  name                  = "test-function"
  description           = "Function to execute test.py"
  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.function_source.name
  source_archive_object = google_storage_bucket_object.function_code.name
  trigger_http          = true
  runtime               = "python310"
  entry_point           = "test_function"

  labels = {
    code_hash = local.source_code_hash
  } 
}

# Enable the Cloud Scheduler and IAM APIs
resource "google_project_service" "scheduler_api" {
  service = "cloudscheduler.googleapis.com"
}

resource "google_project_service" "iam_api" {
  service = "iam.googleapis.com"
}

# Create a Service Account for Cloud Scheduler
resource "google_service_account" "scheduler_invoker" {
  account_id   = "scheduler-invoker"
  display_name = "Scheduler Cloud Function Invoker"
}

# Create a Cloud Scheduler Job
resource "google_cloud_scheduler_job" "daily_function_invocation" {
  name        = "daily-function-invocation"
  description = "Invoke Cloud Function daily"
  schedule    = "0 5 * * *"
  time_zone = "Europe/Berlin"

  http_target {
    http_method = "GET"
    uri         = google_cloudfunctions_function.test_function.https_trigger_url
    oidc_token {
      service_account_email = google_service_account.scheduler_invoker.email
    }
  }
}

# Give the Service Account Permissions to Invoke Cloud Function
resource "google_cloudfunctions_function_iam_member" "invoker" {
  project  = google_cloudfunctions_function.test_function.project
  region   = google_cloudfunctions_function.test_function.region
  cloud_function = google_cloudfunctions_function.test_function.name

  role    = "roles/cloudfunctions.invoker"
  member  = "serviceAccount:${google_service_account.scheduler_invoker.email}"
}

# new secret TRELLO_LIST_ID
resource "google_secret_manager_secret" "trello_list_id_secret" {
  secret_id = "TRELLO_LIST_ID"
  replication {
    auto { }
  }
}

# new secret TRELLO_KEY
resource "google_secret_manager_secret" "trello_key_secret" {
  secret_id = "TRELLO_KEY"
  replication {
    auto {}
  }
}

# new secret TRELLO_TOKEN
resource "google_secret_manager_secret" "trello_token_secret" {
  secret_id = "TRELLO_TOKEN"
  replication {
    auto {}
  }
}

resource "google_storage_bucket" "data_files_bucket" {
  name     = "trellonotify-files-bucket"  # Choose a unique name for your bucket
  location = "us-central1"           # Choose an appropriate region

  # Optional: Enable versioning if you want to keep multiple versions of your data files
  versioning {
    enabled = true
  }

  # Add other configurations as needed
}


# new secret SLACK_API_TOKEN
resource "google_secret_manager_secret" "slack_api_token_secret" {
  secret_id = "SLACK_API_TOKEN"
  replication {
    auto {}
  }
}

# new secret SLACK_CHANNEL_ID
resource "google_secret_manager_secret" "slack_channel_id_secret" {
  secret_id = "SLACK_CHANNEL_ID"
  replication {
    auto {}
  }
}
