#!/bin/bash

# Install system dependencies
sudo yum update -y
sudo amazon-linux-extras install nginx1 -y
sudo yum install -y python3 git

# Configure Python environment
cd web/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure systemd
sudo tee /etc/systemd/system/nitro-web.service <<EOF
[Unit]
Description=Nitro Web Service
After=network.target

[Service]
User=ec2-user
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/gunicorn --bind 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl start nitro-web
sudo systemctl enable nitro-web

# Configure NGINX
sudo tee /etc/nginx/conf.d/nitro-web.conf <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    location /static {
        alias $(pwd)/../frontend;
    }
}
EOF

sudo systemctl restart nginx