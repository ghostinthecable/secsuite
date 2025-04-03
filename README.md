# SecSuite

SecSuite is a monitoring tool designed to collect system metrics and track successful SSH login events. It gathers data such as CPU usage, memory usage, disk usage, load average, and network latency, while also monitoring successful SSH logins. All collected information is stored in a MySQL database for further analysis.

## Features

- **System Metrics Monitoring:**  
  Collects vital metrics including CPU, memory, disk usage, and load average.

- **SSH Login Tracking:**  
  Monitors successful SSH login events to help detect unauthorised access.

- **Dynamic Configuration:**  
  Easily adjust the polling interval and database credentials via configuration files.

- **Systemd Integration:**  
  Runs as a systemd service to ensure continuous monitoring and easy management.

- **Customisable & Extendable:**  
  Designed to integrate seamlessly into various environments with minimal adjustments.

## Installation

### Prerequisites

- **Operating System:** A Linux distribution with access to `/proc` and `/var/log/auth.log`
- **Python:** Version 3.x
- **MySQL:** A MySQL database with a pre-created `secsuite` database and the required table schema
- **Python Module:** Install `mysql-connector-python` (`pip install mysql-connector-python`)
- **Git:** For cloning the repository

### Installation Steps

1. **Create the Base Directory and Clone the Repository**

   Open your terminal and run:
   ```bash
   mkdir -p /opt/secsuite/
   cd /opt/secsuite/
   git clone https://github.com/ghostinthecable/secsuite
   ```

2. **Run the Installation Script**

   Change into the install directory and execute the installation script:
   ```bash
   cd secsuite/install
   bash install_secsuite.sh
   ```

   The installation script will:
   - Verify that the repository is correctly structured in `/opt/secsuite/`
   - Create necessary directories (`bin` and `conf`)
   - Set up default configuration files (`config.ini` and `db.conf`)
   - Create and enable a systemd service for SecSuite

## Configuration

### config.ini

Located at `/opt/secsuite/conf/config.ini`, this file contains general settings. The default polling interval is set to 300 seconds but can be adjusted as needed.

### db.conf

Located at `/opt/secsuite/conf/db.conf`, this file holds your MySQL database credentials. The installation script will prompt you to overwrite this file if it already exists, ensuring you can set your actual credentials.

## Usage

SecSuite runs as a systemd service. You can manage it with the following commands:

```bash
# Check the status of the SecSuite service
systemctl status secsuite

# Restart the SecSuite service
systemctl restart secsuite

# Disable the SecSuite service
systemctl disable secsuite
```

Logs are output to the console and the MySQL database is updated with the latest metrics and SSH login events.

## Contributing

Contributions are welcome! If you wish to enhance SecSuite or report any issues, please fork the repository and submit your pull requests. For major changes, consider opening an issue first to discuss your proposed changes.

## Licence

This software is available for anyone to use, provided that appropriate credit is given to the original author. This project is the property of Orion Security Consulting Limited.

**Attribution:**  
- Original Author: [ghostinthecable](https://x.com/ghostinthecable)  
- Please ensure that any derivative works retain this attribution.

## Contact

For further queries or support, please reach out via my X profile: [x.com/ghostinthecable](https://x.com/ghostinthecable).

