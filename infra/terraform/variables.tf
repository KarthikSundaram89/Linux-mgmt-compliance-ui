# ==============================================================================
# Terraform Variables
# ==============================================================================

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (production, staging)"
  type        = string
  default     = "production"
}

variable "app_name" {
  description = "Application name used for resource naming"
  type        = string
  default     = "linux-inventory"
}

variable "existing_cluster_name" {
  description = "Name of the existing ECS Fargate cluster"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where resources will be deployed"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for ECS tasks"
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for ALB"
  type        = list(string)
}

variable "api_desired_count" {
  description = "Desired number of API tasks"
  type        = number
  default     = 2
}

variable "collector_min_count" {
  description = "Minimum number of collector tasks"
  type        = number
  default     = 1
}

variable "collector_max_count" {
  description = "Maximum number of collector tasks"
  type        = number
  default     = 5
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.small"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 50
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS"
  type        = string
  default     = ""
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the ALB"
  type        = list(string)
  default     = ["10.0.0.0/8"]
}

variable "managed_server_cidr_blocks" {
  description = "CIDR blocks of managed Linux servers (for SSH outbound)"
  type        = list(string)
  default     = ["10.0.0.0/8"]
}

variable "ecr_repo_uri" {
  description = "ECR repository URI for container images"
  type        = string
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Application = "linux-inventory-manager"
    ManagedBy   = "terraform"
  }
}
