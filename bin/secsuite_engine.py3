#!/usr/bin/env python3
"""
SecSuite Engine (v1.2)

This script monitors system metrics (CPU, memory, disk usage, load average, and network latency)
and watches /var/log/auth.log for login events (lines containing "Accepted" or "session opened").
Collected data is stored in a MySQL database using credentials from /opt/secsuite/conf/db.conf.

"""

import os
import time
import threading
import subprocess
import configparser
import datetime
import re
import sys

try:
    import mysql.connector
except ImportError:
    print("Error: mysql.connector module not installed. Please install mysql-connector-python.")
    sys.exit(1)

# File paths
CONFIG_FILE = '/opt/secsuite/conf/config.ini'
DB_CONFIG_FILE = '/opt/secsuite/conf/db.conf'
AUTH_LOG_FILE = '/var/log/auth.log'

def load_polling_interval():
    """Load the polling interval from config.ini (default: 300 seconds)."""
    interval = 300
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        try:
            config.read(CONFIG_FILE)
            interval = config.getint('general', 'polling_interval', fallback=300)
        except Exception as e:
            print("Error reading config.ini; using default polling interval (300 s):", e)
    return interval

def load_db_config():
    """Load database credentials from db.conf."""
    db_config = {}
    if os.path.exists(DB_CONFIG_FILE):
        try:
            with open(DB_CONFIG_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line:
                        key, value = line.split('=', 1)
                        db_config[key.strip()] = value.strip()
        except Exception as e:
            print("Error reading db.conf:", e)
    db_config.setdefault('host', 'localhost')
    db_config.setdefault('database', 'secsuite')
    return db_config

def get_db_connection():
    """Establish and return a connection to the MySQL database.
       IMPORTANT: Make sure your MySQL user is set to use mysql_native_password!
    """
    db_conf = load_db_config()
    try:
        conn = mysql.connector.connect(
            user=db_conf.get('user'),
            password=db_conf.get('password'),
            host=db_conf.get('host'),
            database=db_conf.get('database'),
            ssl_disabled=True,  # This tells the connector not to use SSL.
            use_pure=True
        )
        return conn
    except mysql.connector.Error as err:
        print("Error connecting to database:", err)
        return None

# ------------------ System Metrics Functions ------------------

def get_cpu_usage():
    """Calculate CPU usage percentage by reading /proc/stat twice 1 second apart.
       Returns the percentage of CPU time used.
    """
    try:
        with open('/proc/stat', 'r') as f:
            line = f.readline()
        parts = line.split()
        if parts[0] != 'cpu':
            return 0.0
        total1 = sum(map(int, parts[1:]))
        idle1 = int(parts[4])
        time.sleep(1)
        with open('/proc/stat', 'r') as f:
            line = f.readline()
        parts = line.split()
        total2 = sum(map(int, parts[1:]))
        idle2 = int(parts[4])
        total_diff = total2 - total1
        idle_diff = idle2 - idle1
        if total_diff == 0:
            return 0.0
        usage = (total_diff - idle_diff) / total_diff * 100.0
        return round(usage, 2)
    except Exception as e:
        print("Error calculating CPU usage:", e)
        return 0.0

def get_memory_usage_details():
    """Calculate memory usage details from /proc/meminfo.
       Returns a tuple:
         (memory_percent_used, memory_mb_used, memory_mb_free)
       where the memory values are in megabytes.
    """
    try:
        meminfo = {}
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                parts = line.split(':')
                if len(parts) >= 2:
                    key = parts[0].strip()
                    value = parts[1].strip().split()[0]
                    meminfo[key] = int(value)
        total = meminfo.get('MemTotal', 1)
        available = meminfo.get('MemAvailable', 0)
        used = total - available
        percent = used / total * 100.0
        # Convert from kilobytes to megabytes
        memory_mb_used = used / 1024.0
        memory_mb_free = available / 1024.0
        return round(percent, 2), round(memory_mb_used, 2), round(memory_mb_free, 2)
    except Exception as e:
        print("Error calculating memory usage details:", e)
        return 0.0, 0.0, 0.0

def get_disk_usage_details():
    """Obtain disk usage details for the root filesystem.
       Returns a tuple:
         (disk_percent_used, disk_mb_used, disk_mb_free)
       where the disk values are in megabytes.
    """
    try:
        st = os.statvfs('/')
        total = st.f_blocks * st.f_frsize
        free = st.f_bfree * st.f_frsize
        used = total - free
        percent = used / total * 100.0
        disk_mb_used = used / (1024 * 1024)
        disk_mb_free = free / (1024 * 1024)
        return round(percent, 2), round(disk_mb_used, 2), round(disk_mb_free, 2)
    except Exception as e:
        print("Error calculating disk usage details:", e)
        return 0.0, 0.0, 0.0

def get_load_average():
    """Return the 1-minute load average."""
    try:
        load = os.getloadavg()[0]
        return round(load, 2)
    except Exception as e:
        print("Error getting load average:", e)
        return 0.0

def get_default_gateway():
    """Retrieve the default gateway using 'ip route'."""
    try:
        output = subprocess.check_output("ip route | grep default", shell=True).decode()
        parts = output.split()
        if 'via' in parts:
            return parts[parts.index('via') + 1]
    except Exception as e:
        print("Error getting default gateway:", e)
    return None

def get_latency(host, count=2):
    """Ping a host and return the average latency in milliseconds."""
    try:
        output = subprocess.check_output(f"ping -c {count} -q {host}", shell=True, stderr=subprocess.DEVNULL).decode()
        match = re.search(r"rtt min/avg/max/mdev = [\d\.]+/([\d\.]+)/", output)
        if match:
            return float(match.group(1))
    except Exception as e:
        print(f"Error pinging {host}:", e)
    return None

def poll_system_metrics():
    """Poll system metrics and insert them into the 'system_metrics' table."""
    interval = load_polling_interval()
    while True:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cpu = get_cpu_usage()
        mem_percent, memory_mb_used, memory_mb_free = get_memory_usage_details()
        disk_percent, disk_mb_used, disk_mb_free = get_disk_usage_details()
        load = get_load_average()
        gw = get_default_gateway()
        latency_gw = get_latency(gw) if gw else None
        latency_ext = get_latency("1.1.1.1")
        hostname = os.uname().nodename
        internal_ip = subprocess.getoutput("hostname -I | awk '{print $1}'")
        try:
            external_ip = subprocess.check_output("curl -s https://api.ipify.org", shell=True).decode().strip()
        except Exception:
            external_ip = None

        sql = ("INSERT INTO system_metrics (timestamp, hostname, internal_ip, external_ip, "
               "cpu_percent_used, memory_percent_used, disk_percent_used, load_average, latency_gateway, latency_external, "
               "memory_mb_used, memory_mb_free, disk_mb_used, disk_mb_free) "
               "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
        data = (timestamp, hostname, internal_ip, external_ip,
                cpu, mem_percent, disk_percent, load, latency_gw, latency_ext,
                memory_mb_used, memory_mb_free, disk_mb_used, disk_mb_free)
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(sql, data)
                conn.commit()
                print(f"[{timestamp}] Metrics recorded: CPU {cpu}%, Memory {mem_percent}% ({memory_mb_used} MB used, {memory_mb_free} MB free), "
                      f"Disk {disk_percent}% ({disk_mb_used} MB used, {disk_mb_free} MB free), Load {load}, "
                      f"Latency GW {latency_gw}, Latency 1.1.1.1 {latency_ext}")
                cursor.close()
            except Exception as e:
                print("Error inserting system metrics:", e)
            finally:
                conn.close()
        time.sleep(interval)

def monitor_logins():
    """
    Continuously monitor /var/log/auth.log for successful SSH login events.
    Only lines from sshd containing "Accepted" are inserted into the 'user_logins' table.
    """
    try:
        with open(AUTH_LOG_FILE, 'r') as f:
            f.seek(0, os.SEEK_END)  # start at end of file
            while True:
                line = f.readline()
                if not line:
                    time.sleep(1)
                    continue
                # Filter to include only successful SSH login events
                if "sshd" in line and "Accepted" in line:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    sql = "INSERT INTO user_logins (timestamp, log_entry) VALUES (%s, %s)"
                    data = (timestamp, line.strip())
                    conn = get_db_connection()
                    if conn:
                        try:
                            cursor = conn.cursor()
                            cursor.execute(sql, data)
                            conn.commit()
                            print(f"[{timestamp}] Login event recorded: {line.strip()}")
                            cursor.close()
                        except Exception as e:
                            print("Error inserting login event:", e)
                        finally:
                            conn.close()
    except Exception as e:
        print("Error monitoring logins:", e)

def main():
    # Start threads for system metrics polling and login monitoring.
    t_metrics = threading.Thread(target=poll_system_metrics, daemon=True)
    t_logins = threading.Thread(target=monitor_logins, daemon=True)
    t_metrics.start()
    t_logins.start()
    print("SecSuite Engine started. Monitoring system metrics and user logins.")
    while True:
        time.sleep(60)

if __name__ == '__main__':
    main()
