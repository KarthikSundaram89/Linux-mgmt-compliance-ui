# ==============================================================================
# Terraform Outputs
# ==============================================================================

output "alb_dns_name" {
  description = "ALB DNS name for accessing the application"
  value       = aws_lb.api.dns_name
}

output "sqs_queue_url" {
  description = "SQS queue URL for collection jobs"
  value       = aws_sqs_queue.collections.url
}

output "sqs_dlq_url" {
  description = "SQS dead-letter queue URL"
  value       = aws_sqs_queue.collections_dlq.url
}

output "efs_file_system_id" {
  description = "EFS file system ID for shared storage"
  value       = aws_efs_file_system.storage.id
}

output "efs_access_point_id" {
  description = "EFS access point ID"
  value       = aws_efs_access_point.app.id
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "rds_db_name" {
  description = "RDS database name"
  value       = aws_db_instance.postgres.db_name
}

output "api_security_group_id" {
  description = "Security group for API tasks"
  value       = aws_security_group.api.id
}

output "collector_security_group_id" {
  description = "Security group for collector tasks"
  value       = aws_security_group.collector.id
}

output "api_task_role_arn" {
  description = "IAM role ARN for API task"
  value       = aws_iam_role.api_task.arn
}

output "collector_task_role_arn" {
  description = "IAM role ARN for collector task"
  value       = aws_iam_role.collector_task.arn
}

output "execution_role_arn" {
  description = "IAM role ARN for ECS task execution"
  value       = aws_iam_role.ecs_execution.arn
}
