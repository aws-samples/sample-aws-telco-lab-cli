# Get latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# Security group for bastion host
# SECURITY WARNING: This bastion host provides SSH access to your EKS cluster.
# CUSTOMER RESPONSIBILITY: You must restrict SSH access to your organization's IP ranges.
# AWS provides the security group infrastructure; you are responsible for defining appropriate access rules.
resource "aws_security_group" "bastion" {
  name        = "${var.cluster_name}-bastion-sg"
  description = "Security group for bastion host"
  vpc_id      = var.vpc_id

  # SSH ingress - restricted to allowed CIDR blocks
  # CRITICAL: Never use 0.0.0.0/0 in production. Specify your organization's IP ranges.
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidr_blocks
    description = "SSH access from approved networks only"
  }

  # Egress - allow outbound traffic for package updates and AWS API calls
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic for updates and AWS API access"
  }

  tags = merge(var.tags, {
    Name = "${var.cluster_name}-bastion-sg"
  })
}

# IAM role for bastion host
resource "aws_iam_role" "bastion" {
  name = "${var.cluster_name}-bastion-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# Custom IAM policy for bastion ECR read-only access
# Replaces AmazonEC2ContainerRegistryFullAccess with least-privilege permissions
resource "aws_iam_policy" "bastion_ecr_read" {
  name        = "${var.cluster_name}-bastion-ecr-read"
  description = "Read-only ECR access for bastion host"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:DescribeRepositories",
          "ecr:ListImages"
        ]
        Resource = "*"
      }
    ]
  })

  tags = var.tags
}

# Custom IAM policy for bastion EKS read-only access
# Replaces AmazonEKSClusterPolicy with least-privilege permissions
resource "aws_iam_policy" "bastion_eks_read" {
  name        = "${var.cluster_name}-bastion-eks-read"
  description = "Read-only EKS access for bastion host"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "eks:DescribeCluster",
          "eks:ListClusters",
          "eks:DescribeNodegroup",
          "eks:ListNodegroups",
          "eks:DescribeUpdate",
          "eks:ListUpdates",
          "eks:AccessKubernetesApi"
        ]
        Resource = "arn:aws:eks:${var.aws_region}:*:cluster/*"
      }
    ]
  })

  tags = var.tags
}

# IAM policies for bastion - using custom restrictive policies
resource "aws_iam_role_policy_attachment" "bastion_ecr" {
  policy_arn = aws_iam_policy.bastion_ecr_read.arn
  role       = aws_iam_role.bastion.name
}

resource "aws_iam_role_policy_attachment" "bastion_eks" {
  policy_arn = aws_iam_policy.bastion_eks_read.arn
  role       = aws_iam_role.bastion.name
}

resource "aws_iam_instance_profile" "bastion" {
  name = "${var.cluster_name}-bastion-profile"
  role = aws_iam_role.bastion.name
}

# User data for bastion setup
locals {
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    cluster_name    = var.cluster_name
    cluster_version = var.cluster_version
    aws_region      = var.aws_region
  }))
}

# Bastion host instance
# SECURITY NOTE: Public IP is required for bastion functionality but increases attack surface.
# Ensure security group restricts SSH to approved IP ranges only.
resource "aws_instance" "bastion" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  key_name               = var.key_pair_name
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.bastion.id]
  iam_instance_profile   = aws_iam_instance_profile.bastion.name
  user_data              = local.user_data

  # Public IP required for bastion access
  associate_public_ip_address = true

  # Enable detailed monitoring for security and operational visibility
  monitoring = true

  # Enable EBS optimization for better performance
  ebs_optimized = true

  # Enforce IMDSv2 for enhanced security
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required" # Require IMDSv2
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "enabled"
  }

  root_block_device {
    volume_size = var.volume_size
    volume_type = "gp3"
    encrypted   = true
  }

  tags = merge(var.tags, {
    Name = "${var.cluster_name}-bastion"
  })
}
