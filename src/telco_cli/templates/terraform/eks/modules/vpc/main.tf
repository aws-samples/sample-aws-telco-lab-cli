resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.tags, {
    Name = "${var.tags.Project}-vpc"
  })
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(var.tags, {
    Name = "${var.tags.Project}-igw"
  })
}

resource "aws_subnet" "private" {
  count = length(var.availability_zones)

  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 1)
  availability_zone = var.availability_zones[count.index]

  tags = merge(var.tags, {
    Name = "${var.tags.Project}-private-${count.index + 1}"
    Type = "private"
  })
}

resource "aws_subnet" "public" {
  count = length(var.availability_zones)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = merge(var.tags, {
    Name = "${var.tags.Project}-public-${count.index + 1}"
    Type = "public"
  })
}

# Edge subnet for worker nodes (Region or Outpost)
resource "aws_subnet" "edge" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.edge_subnet_cidr
  availability_zone = var.use_outposts ? var.availability_zones[0] : var.availability_zones[0]
  # Use current account by default, or specified account for RAM shared Outposts
  outpost_arn = var.use_outposts ? "arn:aws:outposts:${data.aws_region.current.id}:${var.outpost_account_id != "" ? var.outpost_account_id : data.aws_caller_identity.current.account_id}:outpost/${var.outpost_id}" : null

  tags = merge(var.tags, {
    Name = "${var.tags.Project}-edge"
    Type = var.use_outposts ? "outpost" : "edge"
  })
}

resource "aws_nat_gateway" "main" {
  count = 1

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = merge(var.tags, {
    Name = "${var.tags.Project}-nat-${count.index + 1}"
  })
}

resource "aws_eip" "nat" {
  count = 1

  domain = "vpc"

  tags = merge(var.tags, {
    Name = "${var.tags.Project}-nat-eip-${count.index + 1}"
  })
}

resource "aws_route_table" "private" {
  count = length(aws_subnet.private)

  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[0].id
  }

  tags = merge(var.tags, {
    Name = "${var.tags.Project}-private-rt-${count.index + 1}"
  })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(var.tags, {
    Name = "${var.tags.Project}-public-rt"
  })
}

resource "aws_route_table_association" "private" {
  count = length(aws_subnet.private)

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "edge" {
  subnet_id      = aws_subnet.edge.id
  route_table_id = var.use_outposts ? aws_route_table.private[0].id : aws_route_table.public.id
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
