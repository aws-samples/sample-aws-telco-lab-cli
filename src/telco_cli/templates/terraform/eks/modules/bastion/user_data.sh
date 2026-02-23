#!/bin/bash
# Bastion Host Setup Script with ECR Management

set -e

# Update system
yum update -y

# Install Docker
amazon-linux-extras install docker -y
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install kubectl (version matches EKS cluster)
KUBECTL_VERSION="${cluster_version}.0"
curl -o kubectl https://amazon-eks.s3.${aws_region}.amazonaws.com/$KUBECTL_VERSION/2024-11-15/bin/linux/amd64/kubectl
chmod +x ./kubectl
mv ./kubectl /usr/local/bin

# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
mv /tmp/eksctl /usr/local/bin

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install

# Install ECR credential helper
yum install -y amazon-ecr-credential-helper

# Configure Docker for ECR
mkdir -p /home/ec2-user/.docker
cat > /home/ec2-user/.docker/config.json << EOF
{
  "credHelpers": {
    "public.ecr.aws": "ecr-login",
    "${aws_region}.amazonaws.com": "ecr-login"
  }
}
EOF
chown -R ec2-user:ec2-user /home/ec2-user/.docker

# ECR Management Functions
cat > /home/ec2-user/.bashrc << 'EOF'
# ECR Management Functions
ecr-login() {
    local region=$${1:-${aws_region}}
    aws ecr get-login-password --region $region | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$region.amazonaws.com
    echo "Logged into ECR in region: $region"
}

ecr-repos() {
    aws ecr describe-repositories --query 'repositories[*].[repositoryName,repositoryUri]' --output table
}

ecr-images() {
    local repo_name=$1
    if [ -z "$repo_name" ]; then
        echo "Usage: ecr-images <repository-name>"
        return 1
    fi
    aws ecr describe-images --repository-name $repo_name --query 'imageDetails[*].[imageTags[0],imagePushedAt,imageSizeInBytes]' --output table
}

ecr-create() {
    local repo_name=$1
    if [ -z "$repo_name" ]; then
        echo "Usage: ecr-create <repository-name>"
        return 1
    fi
    aws ecr create-repository --repository-name $repo_name
    echo "Created ECR repository: $repo_name"
}

ecr-delete() {
    local repo_name=$1
    if [ -z "$repo_name" ]; then
        echo "Usage: ecr-delete <repository-name>"
        return 1
    fi
    aws ecr delete-repository --repository-name $repo_name --force
    echo "Deleted ECR repository: $repo_name"
}

# Auto-configure kubectl on login
if [ -f /home/ec2-user/configure-kubectl.sh ]; then
    /home/ec2-user/configure-kubectl.sh
fi

# Auto-login to ECR
ecr-login
EOF

# Configure kubectl for EKS
cat > /home/ec2-user/configure-kubectl.sh << 'EOF'
#!/bin/bash
aws eks update-kubeconfig --region ${aws_region} --name ${cluster_name}
echo "kubectl configured for cluster: ${cluster_name}"
EOF
chmod +x /home/ec2-user/configure-kubectl.sh
chown ec2-user:ec2-user /home/ec2-user/configure-kubectl.sh

# Set proper ownership
chown ec2-user:ec2-user /home/ec2-user/.bashrc

echo "Bastion host setup complete with ECR management capabilities"
