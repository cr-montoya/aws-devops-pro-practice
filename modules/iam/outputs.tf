output "instance_profile_name" {
  value       = aws_iam_instance_profile.ec2_instance_profile.name
  description = "The name of the IAM instance profile for EC2 instances"
}
