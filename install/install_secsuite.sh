#!/bin/bash
#
# SecSuite Installation Script
#
# This script preps the system by creating working directories, setting up default configuration 
# and credential files, and creating a systemd service for SecSuite.
#
# It assumes that the repository has been cloned into /opt/secsuite/.
#
# Usage:
#   mkdir /opt/secsuite/ ; cd /opt/secsuite
#   git clone https://github.com/ghostinthecable/secsuite
#   cd install ; bash install_secsuite.sh
#
# Ensure the script is run as root.
if [ "$EUID" -ne 0 ]; then
  echo "--------------------------------------------------"
  echo "This script must be run as root. Please run with sudo."
  echo "--------------------------------------------------"
  exit 1
fi

# Define directories and file paths.
BASE_DIR="/opt/secsuite"
BIN_DIR="$BASE_DIR/bin"
CONF_DIR="$BASE_DIR/conf"
SERVICE_FILE="/etc/systemd/system/secsuite.service"
ENGINE_FILE="$BIN_DIR/secsuite_engine.py3"

echo "--------------------------------------------------"
echo "       SecSuite Installation Script"
echo "--------------------------------------------------"
echo ""

echo "Verifying repository structure..."
if [ ! -f "$ENGINE_FILE" ]; then
  echo "Error: Engine file not found at $ENGINE_FILE."
  echo "Please ensure the repository is correctly cloned into $BASE_DIR."
  exit 1
fi
echo "Engine file found at: $ENGINE_FILE"
echo ""

echo "Creating directories..."
mkdir -p "$BIN_DIR" && mkdir -p "$CONF_DIR"
echo "Directories ensured:"
echo "  Binary directory: $BIN_DIR"
echo "  Configuration directory: $CONF_DIR"
echo ""

echo "Setting up configuration files..."
# Create default config.ini if it doesn't exist.
CONFIG_FILE="$CONF_DIR/config.ini"
if [ ! -f "$CONFIG_FILE" ]; then
  cat <<EOF > "$CONFIG_FILE"
[general]
# Polling interval in seconds (default 300 seconds)
polling_interval = 300
EOF
  echo "Default config.ini created at: $CONFIG_FILE"
else
  echo "$CONFIG_FILE already exists. Keeping existing configuration."
fi
echo ""

# Create or prompt for default db.conf.
DB_CONF_FILE="$CONF_DIR/db.conf"
if [ -f "$DB_CONF_FILE" ]; then
  read -p "$DB_CONF_FILE exists. Overwrite with default credentials? [y/N]: " choice
  case "$choice" in
    y|Y )
      cat <<EOF > "$DB_CONF_FILE"
user=your_db_username
password=your_db_password
host=localhost
database=secsuite
EOF
      echo "Default db.conf overwritten. Please edit $DB_CONF_FILE with your actual credentials."
      ;;
    * )
      echo "Keeping existing $DB_CONF_FILE."
      ;;
  esac
else
  cat <<EOF > "$DB_CONF_FILE"
user=your_db_username
password=your_db_password
host=localhost
database=secsuite
EOF
  echo "Default db.conf created at: $DB_CONF_FILE. Please edit it with your actual credentials."
fi
echo ""

echo "Creating systemd service file..."
cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=SecSuite Monitoring Service
After=network.target

[Service]
ExecStart=/usr/bin/env python3 $ENGINE_FILE
WorkingDirectory=$BIN_DIR
Restart=always
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF
echo "Service file created at: $SERVICE_FILE"
echo ""

echo "Reloading systemd daemon..."
systemctl daemon-reload

echo "Enabling and starting SecSuite service..."
systemctl enable secsuite
systemctl restart secsuite

echo "--------------------------------------------------"
echo "Installation complete. SecSuite is now running."
echo "--------------------------------------------------"
