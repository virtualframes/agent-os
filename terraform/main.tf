# Terraform configuration for Agent-OS Infrastructure
# This file defines all necessary cloud resources to run NATS and PostgreSQL on AWS.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
  # Credentials should be configured via environment variables or IAM roles.
}

# --- Networking ---
resource "aws_vpc" "agent_os" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "agent-os-vpc"
  }
}

resource "aws_internet_gateway" "agent_os" {
  vpc_id = aws_vpc.agent_os.id

  tags = {
    Name = "agent-os-igw"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.agent_os.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "agent-os-public"
  }
}

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.agent_os.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name = "agent-os-private-a"
  }
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.agent_os.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = "us-east-1b"

  tags = {
    Name = "agent-os-private-b"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.agent_os.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.agent_os.id
  }

  tags = {
    Name = "agent-os-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.agent_os.id

  tags = {
    Name = "agent-os-private-rt"
  }
}

resource "aws_route_table_association" "private_a" {
  subnet_id      = aws_subnet.private_a.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private_b" {
  subnet_id      = aws_subnet.private_b.id
  route_table_id = aws_route_table.private.id
}

# --- Security Groups ---
resource "aws_security_group" "nats" {
  name        = "agent-os-nats-sg"
  description = "Allow inbound access to NATS"
  vpc_id      = aws_vpc.agent_os.id

  ingress {
    description = "NATS client"
    from_port   = 4222
    to_port     = 4222
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "NATS monitoring"
    from_port   = 8222
    to_port     = 8222
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "agent-os-nats-sg"
  }
}

resource "aws_security_group" "rds" {
  name        = "agent-os-rds-sg"
  description = "Allow PostgreSQL access from NATS instance"
  vpc_id      = aws_vpc.agent_os.id

  ingress {
    description     = "PostgreSQL"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.nats.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "agent-os-rds-sg"
  }
}

# --- Compute ---
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

locals {
  nats_version = "v2.10.7"
}

resource "aws_instance" "nats" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.nats.id]
  key_name               = null

  user_data = <<-EOT
              #!/bin/bash
              set -euxo pipefail

              curl -L -o /tmp/nats-server.tar.gz \
                https://github.com/nats-io/nats-server/releases/download/${local.nats_version}/nats-server-${local.nats_version}-linux-amd64.tar.gz
              tar -xzf /tmp/nats-server.tar.gz -C /tmp
              install -m 0755 /tmp/nats-server-${local.nats_version}-linux-amd64/nats-server /usr/local/bin/nats-server

              cat <<'SERVICE' >/etc/systemd/system/nats.service
              [Unit]
              Description=NATS Server
              After=network.target

              [Service]
              ExecStart=/usr/local/bin/nats-server --jetstream -p 4222 -m 8222
              Restart=on-failure
              LimitNOFILE=65536

              [Install]
              WantedBy=multi-user.target
              SERVICE

              systemctl daemon-reload
              systemctl enable nats.service
              systemctl start nats.service
              EOT

  tags = {
    Name = "agent-os-nats"
  }
}

# --- Database ---
resource "aws_db_subnet_group" "agent_os" {
  name       = "agent-os-db-subnet"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]

  tags = {
    Name = "agent-os-db-subnet"
  }
}

resource "aws_db_instance" "agent_os" {
  identifier              = "agent-os-postgres"
  allocated_storage       = 20
  engine                  = "postgres"
  engine_version          = "15.4"
  instance_class          = "db.t3.micro"
  username                = "agentos"
  password                = "change-me-please"
  db_subnet_group_name    = aws_db_subnet_group.agent_os.name
  vpc_security_group_ids  = [aws_security_group.rds.id]
  publicly_accessible     = false
  skip_final_snapshot     = true
  auto_minor_version_upgrade = true
  backup_retention_period = 0

  tags = {
    Name = "agent-os-postgres"
  }
}
