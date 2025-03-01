#!/bin/bash

# Clear yum locks
sudo rm -f /var/run/yum.pid

# Get absolute project root path
PROJECT_ROOT="/home/ec2-user/NitroCredentialVerification/nitro-web"

# Install dependencies
for i in {1..5}; do
    sudo yum install -y python3 git nginx && break || sleep 15
done

# Configure Python environment
cd "$PROJECT_ROOT/web/backend"
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install requirements
python3 -m pip install --upgrade pip
pip install -r requirements.txt

# Configure systemd
sudo tee /etc/systemd/system/nitro-web.service <<EOF
[Unit]
Description=Nitro Web Service
After=network.target

[Service]
User=ec2-user
WorkingDirectory=$PROJECT_ROOT/web/backend
ExecStart=$PROJECT_ROOT/web/backend/venv/bin/gunicorn --bind 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
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
        alias $PROJECT_ROOT/web/frontend;
        autoindex off;
        expires 1M;
        access_log off;
        add_header Cache-Control "public";
    }
}
EOF

# Set permissions
sudo chown -R ec2-user:ec2-user "$PROJECT_ROOT"
sudo find "$PROJECT_ROOT/web/frontend" -type d -exec chmod 755 {} \;
sudo find "$PROJECT_ROOT/web/frontend" -type f -exec chmod 644 {} \;

# Restart services
sudo systemctl daemon-reload
sudo systemctl enable --now nitro-web
sudo systemctl restart nginx