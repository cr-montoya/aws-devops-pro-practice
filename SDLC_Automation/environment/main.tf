locals {
  app_name = "sldc-automation"
  vpc_cidr = "10.0.0.0/16"
}

data "aws_availability_zones" "available" {
  state = "available"
}

module "vpc" {
  source = "../../modules/network"

  name              = local.app_name
  vpc_cidr          = local.vpc_cidr
  public_subnet_az  = data.aws_availability_zones.available.names[0]
  private_subnet_az = data.aws_availability_zones.available.names[0]
}

module "security_group" {
  source = "../../modules/security_groups"

  name        = "${local.app_name}-sg"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for ${local.app_name} EC2 instances"
  ingress_rules = [
    {
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  ]
}

module "iam" {
  source = "../../modules/iam"
}

module "ec2" {
  source = "../../modules/ec2"

  name                  = "${local.app_name}-instance"
  ami                   = var.ami_id
  instance_type         = "t3.micro"
  subnet_id             = module.vpc.public_subnet_id
  security_group_ids    = [module.security_group.security_group_id]
  associate_public_ip   = true
  root_volume_size      = 8
  root_volume_type      = "gp2"
  instance_count        = 1
  instance_profile_name = module.iam.instance_profile_name
  tags                  = { Environment = "Development" }
}