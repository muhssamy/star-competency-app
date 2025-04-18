// docker/docker-bake.hcl

// Variables with default values
variable "REGISTRY" {
  default = "ghcr.io/muhssamy/star-competency"
}

variable "TAG" {
  default = "latest"
}

variable "DEBUG" {
  default = "False"
}

// App service
target "app" {
  context = "."
  dockerfile = "Dockerfile"
  tags = [
    "${REGISTRY}-app:${TAG}"
  ]
  args = {
    DEBUG = "${DEBUG}"
  }
}

// Backup service
target "backup" {
  context = "."
  dockerfile = "backup.Dockerfile"
  tags = [
    "${REGISTRY}-backup:${TAG}"
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