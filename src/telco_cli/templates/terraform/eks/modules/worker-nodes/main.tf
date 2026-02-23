# Get latest EKS optimized AMI (AL2023 for nodeadm bootstrap)
data "aws_ssm_parameter" "eks_ami" {
  name = "/aws/service/eks/optimized-ami/${var.cluster_version}/amazon-linux-2023/x86_64/standard/recommended/image_id"
}

# Validate AMI exists
data "aws_ami" "eks_ami_validation" {
  owners      = ["amazon"]
  most_recent = true

  filter {
    name   = "image-id"
    values = [data.aws_ssm_parameter.eks_ami.value]
  }
}

# Instance profile for worker nodes
resource "aws_iam_instance_profile" "worker" {
  name = "${var.cluster_name}-worker-profile"
  role = var.worker_role_name
}

# User data for AL2023 with nodeadm bootstrap
locals {
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    cluster_name     = var.cluster_name
    cluster_endpoint = var.cluster_endpoint
    cluster_ca_cert  = var.cluster_ca_certificate
  }))
}

# Launch template for worker nodes
resource "aws_launch_template" "worker" {
  name_prefix   = "${var.cluster_name}-worker-"
  image_id      = data.aws_ssm_parameter.eks_ami.value
  instance_type = var.instance_type
  key_name      = var.key_pair_name
  user_data     = local.user_data

  vpc_security_group_ids = [var.worker_security_group]

  iam_instance_profile {
    name = aws_iam_instance_profile.worker.name
  }

  # Enforce IMDSv2 to prevent SSRF attacks against instance metadata
  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size = var.volume_size
      volume_type = "gp3"
      encrypted   = true
    }
  }

  # Dedicated host placement
  dynamic "placement" {
    for_each = var.use_dedicated_host ? [1] : []
    content {
      host_id = var.dedicated_host_id
    }
  }

  tag_specifications {
    resource_type = "instance"
    tags = merge(var.tags, {
      Name                                        = "${var.cluster_name}-worker"
      "kubernetes.io/cluster/${var.cluster_name}" = "owned"
    })
  }

  tags = var.tags
}

# Auto Scaling Group (only if not using dedicated host)
resource "aws_autoscaling_group" "worker" {
  count = var.use_dedicated_host ? 0 : 1

  name                      = "${var.cluster_name}-worker-asg"
  vpc_zone_identifier       = var.subnet_ids
  target_group_arns         = []
  health_check_type         = "EC2"
  health_check_grace_period = 900

  min_size         = 0
  max_size         = var.desired_capacity * 2
  desired_capacity = var.desired_capacity

  launch_template {
    id      = aws_launch_template.worker.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${var.cluster_name}-worker-asg"
    propagate_at_launch = false
  }

  tag {
    key                 = "kubernetes.io/cluster/${var.cluster_name}"
    value               = "owned"
    propagate_at_launch = true
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Direct EC2 instance for dedicated host
resource "aws_instance" "dedicated_worker" {
  count = var.use_dedicated_host ? var.desired_capacity : 0

  launch_template {
    id      = aws_launch_template.worker.id
    version = "$Latest"
  }

  subnet_id = var.subnet_ids[0]

  # Enforce IMDSv2 explicitly (in addition to launch template setting)
  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  # Enable detailed CloudWatch monitoring (1-minute intervals)
  monitoring = true

  # Enable EBS optimization for better disk I/O
  ebs_optimized = true

  # Ensure root volume is encrypted
  root_block_device {
    encrypted = true
  }

  tags = merge(var.tags, {
    Name                                        = "${var.cluster_name}-dedicated-worker-${count.index + 1}"
    "kubernetes.io/cluster/${var.cluster_name}" = "owned"
  })

  lifecycle {
    create_before_destroy = true
  }
}
