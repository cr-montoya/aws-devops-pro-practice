variable "name" {
  description = "Name tag for the instance(s)"
  type        = string
  default     = "ec2-instance"
}

variable "ami" {
  description = "AMI id to use for the instance. Prefer to pass via TF_VAR_ami or var file."
  type        = string
  default     = ""
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "instance_count" {
  description = "Number of instances to create"
  type        = number
  default     = 1
}

variable "subnet_id" {
  description = "Subnet ID to launch the instance into (optional)"
  type        = string
  default     = ""
}

variable "security_group_ids" {
  description = "List of VPC security group IDs to attach"
  type        = list(string)
  default     = []
}

variable "key_name" {
  description = "Key pair name for SSH access (optional)"
  type        = string
  default     = null
}

variable "user_data" {
  description = "User data script for instance bootstrap (optional)"
  type        = string
  default     = null
}

variable "associate_public_ip" {
  description = "Whether to associate a public IP address"
  type        = bool
  default     = true
}

variable "root_volume_size" {
  description = "Root volume size in GiB"
  type        = number
  default     = 8
}

variable "root_volume_type" {
  description = "Root volume type"
  type        = string
  default     = "gp3"
}

variable "instance_profile_name" {
  description = "IAM instance profile name to attach to the instance (optional)"
  type        = string
  default     = null
}

variable "tags" {
  description = "Additional tags to apply to the instance"
  type        = map(string)
  default     = {}
}
