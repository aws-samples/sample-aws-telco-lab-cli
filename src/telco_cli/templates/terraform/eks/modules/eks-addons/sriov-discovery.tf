# SR-IOV Device Discovery via SSM using null_resource
resource "null_resource" "discover_sriov" {
  count = var.enable_sriov_discovery && length(var.worker_instance_ids) > 0 ? 1 : 0

  provisioner "local-exec" {
    command = <<-EOT
      COMMAND_ID=$(aws ssm send-command \
        --document-name "AWS-RunShellScript" \
        --instance-ids ${var.worker_instance_ids[0]} \
        --parameters 'commands=["for pci in $(lspci -nn | grep -E \"Ethernet|Network\" | grep -v ENA | awk \"{print \\$1}\"); do vendor=$(lspci -s $pci -n | awk \"{print \\$3}\" | cut -d: -f1); device=$(lspci -s $pci -n | awk \"{print \\$3}\" | cut -d: -f2); driver=$(lspci -k -s $pci | grep \"Kernel driver\" | awk \"{print \\$5}\" || echo \"none\"); echo \"$pci,$vendor,$device,$driver\"; done"]' \
        --region us-east-1 \
        --query 'Command.CommandId' \
        --output text)
      
      sleep 10
      
      aws ssm get-command-invocation \
        --command-id $COMMAND_ID \
        --instance-id ${var.worker_instance_ids[0]} \
        --region us-east-1 \
        --query 'StandardOutputContent' \
        --output text > /tmp/sriov_discovery_${count.index}.txt
    EOT
  }

  triggers = {
    instance_ids = join(",", var.worker_instance_ids)
  }
}

# Use external data source to parse the discovery results
data "external" "sriov_discovery" {
  count = var.enable_sriov_discovery && length(var.worker_instance_ids) > 0 ? 1 : 0

  program = ["bash", "-c", <<-EOT
    if [ -f "/tmp/sriov_discovery_${count.index}.txt" ]; then
      # Parse CSV output into JSON
      echo '{"devices":['
      first=true
      while IFS=',' read -r pci vendor device driver; do
        if [ "$first" = true ]; then first=false; else echo ','; fi
        echo -n "{\"pci\":\"$pci\",\"vendor\":\"$vendor\",\"device\":\"$device\",\"driver\":\"$driver\"}"
      done < /tmp/sriov_discovery_${count.index}.txt
      echo ']}'
    else
      # Fallback to known devices
      echo '{"devices":[{"pci":"0000:02:00.0","vendor":"15b3","device":"1021","driver":"mlx5_core"}]}'
    fi
  EOT
  ]

  depends_on = [null_resource.discover_sriov]
}

# Parse discovered devices and generate SR-IOV config
locals {
  # Use discovered devices or fallback to static config
  sriov_devices = var.enable_sriov_discovery && length(var.worker_instance_ids) > 0 ? jsondecode(data.external.sriov_discovery[0].result.devices) : {
    devices = [
      {
        pci    = "0000:02:00.0"
        vendor = "15b3"
        device = "1021"
        driver = "mlx5_core"
      }
    ]
  }

  # Filter SR-IOV capable devices (exclude ENA)
  sriov_capable_devices = [
    for device in local.sriov_devices.devices : device
    if device.vendor != "1d0f" && device.driver != "ena" && device.driver != "none"
  ]

  # Generate resource list for SR-IOV device plugin
  sriov_resource_list = [
    for device in local.sriov_capable_devices : {
      resourceName = "mellanox_sriov_netdevice"
      selectors = {
        vendors = [device.vendor]
        devices = [device.device]
        drivers = [device.driver]
      }
    }
  ]
}
