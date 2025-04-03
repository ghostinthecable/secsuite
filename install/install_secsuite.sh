#!/bin/bash
#
# SecSuite Installation Script
#
# This script preps the system by creating the necessary directories, setting up default
# configuration and credential files, and creating a systemd service for SecSuite.
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

echo "Setting up database configuration..."
DB_CONF_FILE="$CONF_DIR/db.conf"
INITIALISE_DB=false

if [ -f "$DB_CONF_FILE" ]; then
  read -p "$DB_CONF_FILE exists. Overwrite with new credentials? [y/N]: " choice
  case "$choice" in
    y|Y )
      read -p "Enter DB username: " DB_USER
      read -s -p "Enter DB password: " DB_PASS; echo
      DB_HOST="localhost"
      DB_NAME="secsuite"
      cat <<EOF > "$DB_CONF_FILE"
user=$DB_USER
password=$DB_PASS
host=$DB_HOST
database=$DB_NAME
EOF
      echo "Credentials saved to $DB_CONF_FILE."
      INITIALISE_DB=true
      ;;
    * )
      echo "Keeping existing $DB_CONF_FILE."
      read -p "Would you like to refresh the database schema from db/secsuite.sql? [y/N]: " refresh_choice
      [[ "$refresh_choice" =~ ^[yY]$ ]] && INITIALISE_DB=true
      ;;
  esac
else
  read -p "Enter DB username: " DB_USER
  read -s -p "Enter DB password: " DB_PASS; echo
  DB_HOST="localhost"
  DB_NAME="secsuite"
  cat <<EOF > "$DB_CONF_FILE"
user=$DB_USER
password=$DB_PASS
host=$DB_HOST
database=$DB_NAME
EOF
  echo "Credentials saved to $DB_CONF_FILE."
  INITIALISE_DB=true
fi

echo ""

# Initialise the database schema if requested.
if $INITIALISE_DB ; then
  echo "Initialising database schema from db/secsuite.sql..."
  # Extract credentials from the configuration file.
  DB_USER=$(grep '^user=' "$DB_CONF_FILE" | cut -d '=' -f2)
  DB_PASS=$(grep '^password=' "$DB_CONF_FILE" | cut -d '=' -f2)
  DB_NAME=$(grep '^database=' "$DB_CONF_FILE" | cut -d '=' -f2)

  if [ ! -f "$BASE_DIR/db/secsuite.sql" ]; then
    echo "Error: Database schema file not found at $BASE_DIR/db/secsuite.sql."
  else
    mysql -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" < "$BASE_DIR/db/secsuite.sql" 2>/dev/null

    if [ $? -eq 0 ]; then
      echo "Database initialised successfully."
    else
      echo "Error: Failed to initialise the database. Please check your credentials or the schema file."
    fi
  fi
fi

echo ""

echo "Checking for Python MySQL connector (mysql-connector-python)..."
if ! python3 -c "import mysql.connector" 2>/dev/null; then
  echo "mysql-connector-python not found. Installing..."
  sudo apt install python3-mysql.connector -y
else
  echo "mysql-connector-python already installed."
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
