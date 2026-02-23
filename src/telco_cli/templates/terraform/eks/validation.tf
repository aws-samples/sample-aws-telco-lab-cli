# Validation logic for Terraform variables
locals {
  validation_errors = compact([
    var.use_outposts && var.outpost_id == "" ? "outpost_id required when use_outposts=true" : "",
    var.use_dedicated_host && var.dedicated_host_id == "" ? "dedicated_host_id required when use_dedicated_host=true" : "",
    !var.deploy_vpc && var.existing_vpc_id == "" ? "existing_vpc_id required when deploy_vpc=false" : "",
    var.use_outposts && var.outpost_account_id == "" ? "outpost_account_id required when use_outposts=true" : ""
  ])
}

# Validation check - fails deployment if errors exist
resource "null_resource" "validation" {
  count = length(local.validation_errors) > 0 ? 1 : 0

  provisioner "local-exec" {
    command = "echo 'Validation errors: ${join(", ", local.validation_errors)}' && exit 1"
  }
}