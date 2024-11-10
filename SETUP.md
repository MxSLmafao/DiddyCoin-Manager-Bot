# DiddyCoin Discord Bot - Ubuntu VPS Setup Guide

This guide explains how to set up and run the DiddyCoin Discord bot on an Ubuntu VPS.

## System Requirements

- Ubuntu 20.04 LTS or newer
- Minimum 1GB RAM
- 10GB storage space

## Prerequisites

1. A Discord bot token (from Discord Developer Portal)
2. PostgreSQL database credentials

## Installation Steps

### 1. System Updates and Dependencies

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip postgresql postgresql-contrib git
```

### 2. PostgreSQL Database Setup

```bash
# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE USER diddybot WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "CREATE DATABASE diddycoin OWNER diddybot;"
```

### 3. Clone and Setup Bot

```bash
# Clone repository
git clone <your-repository-url>
cd diddy-bot

# Install Python dependencies
pip3 install -r requirements.txt
```

### 4. Configuration

1. Create environment variables file:
```bash
cat > .env << EOL
DISCORD_TOKEN=your_discord_token
PGUSER=diddybot
PGPASSWORD=your_password
PGDATABASE=diddycoin
PGHOST=localhost
PGPORT=5432
EOL
```

2. Update config.yaml with your admin Discord ID:
```yaml
bot:
  admin_ids: [your_discord_id]  # Replace with your Discord ID
```

### 5. Create Systemd Service

Create a service file for automatic startup:

```bash
sudo nano /etc/systemd/system/diddybot.service
```

Add the following content:

```ini
[Unit]
Description=DiddyCoin Discord Bot
After=network.target postgresql.service

[Service]
User=your_username
WorkingDirectory=/path/to/diddy-bot
Environment=DISCORD_TOKEN=your_discord_token
Environment=PGUSER=diddybot
Environment=PGPASSWORD=your_password
Environment=PGDATABASE=diddycoin
Environment=PGHOST=localhost
Environment=PGPORT=5432
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 6. Start the Bot Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable and start the service
sudo systemctl enable diddybot
sudo systemctl start diddybot
```

### 7. Monitoring and Maintenance

Check bot status:
```bash
sudo systemctl status diddybot
```

View logs:
```bash
journalctl -u diddybot -f
```

## Security Considerations

1. Use strong passwords for PostgreSQL
2. Keep your Discord token secure
3. Regularly update system packages
4. Enable UFW firewall:
```bash
sudo ufw enable
sudo ufw allow ssh
```

## Troubleshooting

1. If bot fails to start, check logs:
```bash
journalctl -u diddybot -n 50
```

2. Database connection issues:
```bash
sudo -u postgres psql -c "\l" # List databases
sudo -u postgres psql -c "\du" # List users
```

3. Service not starting:
```bash
sudo systemctl restart diddybot
systemctl status diddybot
```

## Backup and Recovery

1. Database backup:
```bash
pg_dump -U diddybot diddycoin > backup.sql
```

2. Database restore:
```bash
psql -U diddybot diddycoin < backup.sql
```

## Updating the Bot

1. Stop the service:
```bash
sudo systemctl stop diddybot
```

2. Pull updates:
```bash
cd /path/to/diddy-bot
git pull origin main
```

3. Restart service:
```bash
sudo systemctl restart diddybot
```
