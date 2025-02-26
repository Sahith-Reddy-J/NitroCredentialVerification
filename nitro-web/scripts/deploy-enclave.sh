#!/bin/bash

# Clean existing yum locks
sudo rm -f /var/run/yum.pid

# Set default locale
export LC_ALL=C

# Install base dependencies
sudo yum update -y
sudo amazon-linux-extras install docker -y
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user

# Install jq with explicit dependencies
sudo yum install -y oniguruma
sudo yum install -y jq

# Install Nitro CLI (verify region matches your instance)
# AWS_REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)
# NITRO_CLI_URL="https://aws-nitro-enclaves-cli-${AWS_REGION}.s3.${AWS_REGION}.amazonaws.com/aws-nitro-enclaves-cli-latest.x86_64.rpm"
# sudo yum install -y "$NITRO_CLI_URL"
sudo amazon-linux-extras enable aws-nitro-enclaves-cli
sudo amazon-linux-extras install aws-nitro-enclaves-cli -y
sudo yum install aws-nitro-enclaves-cli-devel -y
sudo usermod -aG ne ec2-user
sudo systemctl enable nitro-enclaves-allocator.service
sudo systemctl start nitro-enclaves-allocator.service

# Verify Nitro CLI installation
sudo nitro-cli --version

# Build enclave image
cd enclave
sudo docker build -t skill-signer .

# Build EIF with explicit parameters
sudo nitro-cli build-enclave \
  --docker-uri skill-signer:latest \
  --output-file enclave.eif 

# Terminate existing enclaves
sudo nitro-cli terminate-enclave --all || true

# Run enclave with debug
sudo nitro-cli run-enclave \
  --eif-path enclave.eif \
  --memory 512 \
  --cpu-count 2 \
  --debug-mode &

# Wait for enclave initialization
sleep 15

# Fetch public key from correct path
cd ..
python3 - <<EOF
import sys
sys.path.append('web/backend')
from client import get_public_key

pubkey = get_public_key()
with open("public_key.pem", "w") as f:
    f.write(pubkey)
EOF