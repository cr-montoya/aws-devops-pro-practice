terraform {
  backend "s3" {
    bucket       = "aws-dop-co02-practice-terraform-state"
    key          = "sldc_automation.tfstate"
    region       = "us-east-2"
    use_lockfile = true
    encrypt      = true
  }
}