variable "name" {
  description = "Name prefix for resources"
  type        = string
  default     = "simple-sg"
}

variable "description" {
  description = "Description for the security group"
  type        = string
  default     = "Security group managed by Terraform"
}

variable "vpc_id" {
  description = "VPC ID where the security group will be created"
  type        = string
  default     = ""
}

variable "ingress_rules" {
  description = "List of ingress rules for the security group"
  type = list(object({
    from_port   = number
    to_port     = number
    protocol    = string
    cidr_blocks = list(string)
  }))
  default = []
}

variable "tags" {
  description = "Additional tags to apply"
  type        = map(string)
  default     = {}
}