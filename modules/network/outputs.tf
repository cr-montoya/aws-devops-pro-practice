output "vpc_id" {
  description = "VPC id"
  value       = aws_vpc.this.id
}

output "internet_gateway_id" {
  description = "Internet Gateway id"
  value       = aws_internet_gateway.this.id
}

output "public_subnet_id" {
  description = "Public subnet id"
  value       = aws_subnet.public.id
}

output "private_subnet_id" {
  description = "Private subnet id"
  value       = aws_subnet.private.id
}

output "public_route_table_id" {
  description = "Public route table id"
  value       = aws_route_table.public.id
}

output "private_route_table_id" {
  description = "Private route table id"
  value       = aws_route_table.private.id
}
