variable "name" {
  description = "Name prefix for resources"
  type        = string
  default     = "simple-network"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_az" {
  description = "(Optional) availability zone for the public subnet"
  type        = string
  default     = ""
}

variable "private_subnet_az" {
  description = "(Optional) availability zone for the private subnet"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Additional tags to apply"
  type        = map(string)
  default     = {}
}
