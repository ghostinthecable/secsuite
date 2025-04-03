#!/usr/bin/env python3
"""
display_overview.py3

This script connects to the MySQL database using credentials specified in
the configuration file (conf/db.conf), retrieves system metrics from the last
10 minutes and the last 5 user login events, then prints a nicely formatted
overview in the terminal.

Metrics are displayed as ASCII bar graphs and the latest login events are listed.
"""

import mysql.connector
import os
import sys
import datetime

def load_db_config():
    """Load database credentials from the configuration file (conf/db.conf)."""
    db_config = {}
    config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "conf", "db.conf")
    if not os.path.isfile(config_path):
        print(f"Database configuration file not found at {config_path}.")
        sys.exit(1)
    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line:
                    key, value = line.split('=', 1)
                    db_config[key.strip()] = value.strip()
    except Exception as e:
        print("Error reading db.conf:", e)
        sys.exit(1)
    db_config.setdefault('host', 'localhost')
    db_config.setdefault('database', 'secsuite')
    return db_config

def get_db_connection():
    """Establish and return a connection to the MySQL database.

    IMPORTANT: Ensure that your MySQL user is set to use mysql_native_password.
    """
    db_conf = load_db_config()
    try:
        conn = mysql.connector.connect(
            user=db_conf.get('user'),
            password=db_conf.get('password'),
            host=db_conf.get('host'),
            database=db_conf.get('database'),
            ssl_disabled=True,  # Disable SSL as per engine configuration.
            use_pure=True
        )
        return conn
    except mysql.connector.Error as err:
        print("Error connecting to database:", err)
        sys.exit(1)

def ascii_bar(value, width=50):
    """Return an ASCII bar graph representation for a value between 0 and 100."""
    bar_length = int((value / 100) * width)
    return "#" * bar_length + "-" * (width - bar_length)

def display_metrics():
    """Query and display system metrics from the last 10 minutes as ASCII graphs."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtain the hostname from the system (assumes metrics are recorded per host).
    hostname = os.uname().nodename

    # Query for metrics in the last 10 minutes for this host.
    query = (
        "SELECT timestamp, cpu_percent_used, memory_percent_used, disk_percent_used "
        "FROM system_metrics "
        "WHERE hostname = %s AND timestamp >= (NOW() - INTERVAL 10 MINUTE) "
        "ORDER BY timestamp ASC;"
    )
    cursor.execute(query, (hostname,))
    metrics = cursor.fetchall()

    print(f"\nHost: {hostname}\n")
    print("Metrics from last 10 minutes:\n")

    if not metrics:
        print("No metrics found in the last 10 minutes.\n")
    else:
        # Prepare data lists for each metric.
        cpu_data = []
        mem_data = []
        disk_data = []
        for row in metrics:
            ts, cpu, mem, disk = row
            # Format timestamp to HH:MM:SS.
            if isinstance(ts, datetime.datetime):
                time_str = ts.strftime("%H:%M:%S")
            else:
                time_str = ts[11:19]
            cpu_data.append((time_str, cpu))
            mem_data.append((time_str, mem))
            disk_data.append((time_str, disk))

        def print_graph(title, data):
            print(title)
            for time_str, value in data:
                bar = ascii_bar(value)
                print(f"{time_str} | {bar} | {value:.2f}%")
            print("")

        print_graph("CPU Usage:", cpu_data)
        print_graph("Memory Usage:", mem_data)
        print_graph("Disk Usage:", disk_data)

    cursor.close()
    conn.close()

def display_logins():
    """Query and display the last 5 user login events."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT timestamp, log_entry FROM user_logins ORDER BY timestamp DESC LIMIT 5;"
    cursor.execute(query)
    logins = cursor.fetchall()

    print("Last 5 Logins:\n")
    if not logins:
        print("No login events found.\n")
    else:
        for ts, log in logins:
            if isinstance(ts, datetime.datetime):
                time_str = ts.strftime("%Y-%m-%d %H:%M:%S")
            else:
                time_str = ts
            print(f"{time_str} - {log}")
        print("")

    cursor.close()
    conn.close()

def main():
    display_metrics()
    display_logins()

if __name__ == '__main__':
    main()
