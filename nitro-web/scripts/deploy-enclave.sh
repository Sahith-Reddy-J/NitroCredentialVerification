#!/bin/bash

# Install dependencies
sudo yum update -y
sudo amazon-linux-extras install docker -y
sudo systemctl start docker
sudo usermod -aG docker $USER
sudo yum install -y jq

# Install Nitro CLI
sudo yum install -y https://aws-nitro-enclaves-cli-us-east-1.s3.us-east-1.amazonaws.com/aws-nitro-enclaves-cli-latest.x86_64.rpm

# Build enclave
cd enclave
sudo docker build -t skill-signer .

# Create EIF
sudo nitro-cli build-enclave \
  --docker-uri skill-signer:latest \
  --output-file enclave.eif \
  --memory 2048 \
  --cpu-count 2

# Terminate existing enclaves
sudo nitro-cli terminate-enclave --all

# Start enclave
sudo nitro-cli run-enclave \
  --eif-path enclave.eif \
  --memory 2048 \
  --cpu-count 2 \
  --debug-mode &

# Wait for initialization
sleep 15

# Fetch public key
python3 ../scripts/fetch-pubkey.py