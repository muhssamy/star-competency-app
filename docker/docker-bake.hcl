// Variables with default values
variable "REGISTRY" {
  default = ""
}

variable "TAG" {
  default = "latest"
}

variable "DEBUG" {
  default = "False"
}

// Common build settings
target "common" {
  context = ".."
}

// App service
target "app" {
  inherits = ["common"]
  dockerfile = "docker/Dockerfile"
  tags = [
    "${REGISTRY}star-competency-app:${TAG}"
  ]
  args = {
    DEBUG = "${DEBUG}"
  }
}

// Backup service
target "backup" {
  inherits = ["common"]
  dockerfile = "docker/backup.Dockerfile"
  tags = [
    "${REGISTRY}star-competency-backup:${TAG}"
  ]
}

// Default group builds all services
group "default" {
  targets = ["app", "backup"]
}

// Development preset
group "dev" {
  targets = ["app", "backup"]
  args = {
    DEBUG = "True"
    TAG = "dev"
  }
}

// Production preset
group "prod" {
  targets = ["app", "backup"]
  args = {
    DEBUG = "False"
    TAG = "prod"
  }
}