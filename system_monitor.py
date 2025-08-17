#   system_monitor.py - System Resource Monitoring and Alerting
import os
import psutil
import time
import logging
import sqlite3
import datetime
import requests  #   Import the requests module
import socket  #   Import the socket module

#   Configure logging
logging.basicConfig(
    filename='system_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    encoding='utf-8'
)

DB_PATH = "/home/onkar/Monitoring_script/logs/monitoring_data.db"  #   Database path

#   Alert Thresholds
WARNING_CPU_TEMP = 60
CRITICAL_CPU_TEMP = 65
WARNING_RAM_USAGE =70
CRITICAL_RAM_USAGE = 80
WARNING_STORAGE_USAGE = 70
CRITICAL_STORAGE_USAGE = 80

import psutil

#   --- Alert Storage ---
stored_alerts = []  #   Initialize an empty list to store alerts

def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def get_ram_usage():
    return psutil.virtual_memory().percent

def get_disk_usage():
    return psutil.disk_usage('/').percent

def get_temperature():
    try:
        temp = psutil.sensors_temperatures().get('cpu_thermal', [{}])[0].get('current', None)
        return temp if temp else "N/A"
    except AttributeError:
        return "N/A"

def create_table():
    """Creates the system_resources table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_resources (
            timestamp TEXT,
            cpu_temp REAL,
            cpu_usage REAL,
            ram_usage REAL,
            storage_usage REAL
        )
    ''')
    conn.commit()
    conn.close()

def get_cpu_temperature():
    """Get the CPU temperature using vcgencmd (Raspberry Pi)."""
    try:
        res = os.popen('vcgencmd measure_temp').readline()
        temp_str = res.replace("temp=", "").replace("'C\n", "")
        return float(temp_str)
    except Exception as e:
        logging.error(f"Failed to get CPU temperature: {e}")
        return None

def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def get_ram_usage():
    mem = psutil.virtual_memory()
    return mem.total, mem.used, mem.percent

def get_storage_usage():
    disk = psutil.disk_usage('/')
    return disk.total, disk.used, disk.percent

def save_to_db(cpu_temp, cpu_usage, ram_percent, storage_percent):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO system_resources (timestamp, cpu_temp, cpu_usage, ram_usage, storage_usage) VALUES (?, ?, ?, ?, ?)",
        (timestamp, cpu_temp, cpu_usage, ram_percent, storage_percent)
    )
    conn.commit()
    conn.close()

def check_and_send_alerts(cpu_temp, ram_percent, storage_percent):
    """
    Checks system metrics against thresholds and logs alerts.
    Also stores critical alerts in the stored_alerts list.
    """
    global stored_alerts  #   Use the global stored_alerts list

    if cpu_temp is not None:
        if cpu_temp >= CRITICAL_CPU_TEMP:
            alert_message = f"? CRITICAL: CPU Temperature {cpu_temp:.1f} \u00B0C (Threshold: {CRITICAL_CPU_TEMP} \u00B0C)"
            logging.critical(alert_message)
            stored_alerts.append(alert_message)  #   Store the alert
        elif cpu_temp >= WARNING_CPU_TEMP:
            logging.warning(f"?? WARNING: CPU Temperature {cpu_temp:.1f} \u00B0C (Threshold: {WARNING_CPU_TEMP} \u00B0C)")

    if ram_percent >= CRITICAL_RAM_USAGE:
        alert_message = f"? CRITICAL: RAM Usage {ram_percent:.1f}% (Threshold: {CRITICAL_RAM_USAGE}%)"
        logging.critical(alert_message)
        stored_alerts.append(alert_message)  #   Store the alert
    elif ram_percent >= WARNING_RAM_USAGE:
        logging.warning(f"?? WARNING: RAM Usage {ram_percent:.1f}% (Threshold: {WARNING_RAM_USAGE}%)")

    if storage_percent >= CRITICAL_STORAGE_USAGE:
        alert_message = f"? CRITICAL: Storage Usage {storage_percent:.1f}% (Threshold: {CRITICAL_STORAGE_USAGE}%)"
        logging.critical(alert_message)
        stored_alerts.append(alert_message)  #   Store the alert
    elif storage_percent >= WARNING_STORAGE_USAGE:
        logging.warning(f"?? WARNING: Storage Usage {storage_percent:.1f}% (Threshold: {WARNING_STORAGE_USAGE}%)")

def get_uptime():
    """
    Calculates system uptime.
    """
    return time.time() - psutil.boot_time()

def format_uptime(uptime_seconds):
    """
    Formats uptime in a human-readable format.
    """
    days = int(uptime_seconds // (60 * 60 * 24))
    hours = int((uptime_seconds % (60 * 60 * 24)) // (60 * 60))
    minutes = int((uptime_seconds % (60 * 60)) // 60)
    seconds = int(uptime_seconds % 60)

    uptime_str = ""
    if days > 0:
        uptime_str += f"{days} days, "
    if hours > 0:
        uptime_str += f"{hours} hours, "
    if minutes > 0:
        uptime_str += f"{minutes} minutes, "
    uptime_str += f"{seconds} seconds"
    return uptime_str

def log_system_metrics():
    try:
        cpu_temp = get_cpu_temperature()
        cpu_usage = get_cpu_usage()
        ram_total, ram_used, ram_percent = get_ram_usage()
        storage_total, storage_used, storage_percent = get_storage_usage()

        if cpu_temp is not None:
            cpu_temp_str = f"{cpu_temp:.1f} \u00B0C"  #   Display in Celsius
        else:
            cpu_temp_str = "N/A"

        log_message = (f"CPU Temp: {cpu_temp_str} | CPU Usage: {cpu_usage:.1f}% | "
                       f"RAM: {ram_used / (1024 ** 2):.2f} MB / {ram_total / (1024 ** 2):.2f} MB ({ram_percent:.1f}%) | "
                       f"Storage: {storage_used / (1024 ** 3):.2f} GB / {storage_total / (1024 ** 3):.2f} GB ({storage_percent:.1f}%)")

        print(log_message)
        logging.info(log_message)

        save_to_db(cpu_temp, cpu_usage, ram_percent, storage_percent)

        #   Preserve original functionality: Log warnings/criticals
        if cpu_temp is not None:
            if cpu_temp >= CRITICAL_CPU_TEMP:
                alert_message = f"? CRITICAL: CPU Temperature {cpu_temp:.1f} \u00B0C (Threshold: {CRITICAL_CPU_TEMP} \u00B0C)"
                logging.critical(alert_message)
            elif cpu_temp >= WARNING_CPU_TEMP:
                logging.warning(f"?? WARNING: CPU Temperature {cpu_temp:.1f} \u00B0C (Threshold: {WARNING_CPU_TEMP} \u00B0C)")

        if ram_percent >= CRITICAL_RAM_USAGE:
            alert_message = f"? CRITICAL: RAM Usage {ram_percent:.1f}% (Threshold: {CRITICAL_RAM_USAGE}%)"
            logging.critical(alert_message)
        elif ram_percent >= WARNING_RAM_USAGE:
            logging.warning(f"?? WARNING: RAM Usage {ram_percent:.1f}% (Threshold: {WARNING_RAM_USAGE}%)")

        if storage_percent >= CRITICAL_STORAGE_USAGE:
            alert_message = f"? CRITICAL: Storage Usage {storage_percent:.1f}% (Threshold: {CRITICAL_STORAGE_USAGE}%)"
            logging.critical(alert_message)
        elif storage_percent >= WARNING_STORAGE_USAGE:
            logging.warning(f"?? WARNING: Storage Usage {storage_percent:.1f}% (Threshold: {WARNING_STORAGE_USAGE}%)")

        #   ALSO call the alert checking function (for external modules or new functionality)
        check_and_send_alerts(cpu_temp, ram_percent, storage_percent)

    except Exception as e:
        logging.exception(f"Error in log_system_metrics: {e}")

def get_system_status():
    """
    Returns system metrics as a formatted string, including uptime.
    """
    cpu_temp = get_cpu_temperature()
    cpu_usage = get_cpu_usage()
    ram_total, ram_used, ram_percent = get_ram_usage()
    storage_total, storage_used, storage_percent = get_storage_usage()
    uptime_seconds = get_uptime()
    uptime_string = format_uptime(uptime_seconds)

    system_status = (
        f" System Status\n"
        f" CPU Temp: {cpu_temp:.1f}\u00B0CC\n"
        f" CPU Usage: {cpu_usage:.1f}%\n"
        f" RAM: {ram_used / (1024 ** 2):.2f} MB / {ram_total / (1024 ** 2):.2f} MB ({ram_percent:.1f}%)\n"
        f" Storage: {storage_used / (1024 ** 3):.2f} GB / {storage_total / (1024 ** 3):.2f} GB ({storage_percent:.1f}%)\n"
        f" Uptime: {uptime_string}\n"  #   Added Uptime
    )

    return system_status

#   --- IP Address Functions ---
def get_public_ip():
    """
    Retrieves the public IP address.
    """
    try:
        response = requests.get('https://api.ipify.org')
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching public IP: {e}")
        return "Error fetching public IP"

def get_private_ip():
    """
    Retrieves all private IP addresses excluding loopback (127.*) and APIPA (169.*).
    """
    private_ips = []
    try:
        #   Get all network interfaces
        for iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                #   Check if the address is an IPv4 address and not a loopback or APIPA address
                if addr.family == socket.AF_INET:
                    ip = addr.address
                    if not (ip.startswith('127.') or ip.startswith('169.')):
                        private_ips.append(ip)
        
        return private_ips if private_ips else "Private IP not found"
    
    except Exception as e:
        logging.error(f"Error fetching private IP: {e}")
        return "Error fetching private IP"


#   --- New Functionalities ---

def set_alert_threshold(metric, threshold_type, value):
    """
    Allows setting alert thresholds dynamically.
    metric: "cpu_temp", "ram_usage", "storage_usage"
    threshold_type: "warning", "critical"
    value:  The new threshold value
    """
    global WARNING_CPU_TEMP, CRITICAL_CPU_TEMP, WARNING_RAM_USAGE, CRITICAL_RAM_USAGE, WARNING_STORAGE_USAGE, CRITICAL_STORAGE_USAGE

    try:
        value = float(value)  #   Ensure the value is a number
    except ValueError:
        logging.error(f"Invalid threshold value: {value}")
        return False

    if metric == "cpu_temp":
        if threshold_type == "warning":
            WARNING_CPU_TEMP = value
        elif threshold_type == "critical":
            CRITICAL_CPU_TEMP = value
        else:
            logging.error(f"Invalid threshold type: {threshold_type}")
            return False
    elif metric == "ram_usage":
        if threshold_type == "warning":
            WARNING_RAM_USAGE = value
        elif threshold_type == "critical":
            CRITICAL_RAM_USAGE = value
        else:
            logging.error(f"Invalid threshold type: {threshold_type}")
            return False
    elif metric == "storage_usage":
        if threshold_type == "warning":
            WARNING_STORAGE_USAGE = value
        elif threshold_type == "critical":
            CRITICAL_STORAGE_USAGE = value
        else:
            logging.error(f"Invalid threshold type: {threshold_type}")
            return False
    else:
        logging.error(f"Invalid metric: {metric}")
        return False

    logging.info(f"Threshold for {metric} ({threshold_type}) set to {value}")
    return True

def get_stored_alerts():
    """
    Retrieves the stored critical alerts.
    """
    global stored_alerts
    alerts = stored_alerts
    stored_alerts = []  #   Clear the alerts after retrieving them
    return alerts

#   Example of a new function to get alert history (this is a placeholder - you'd need to implement actual retrieval)
def get_alert_history(time_period):
    """
    Retrieves alert history (This is a placeholder - implement actual retrieval).
    time_period: "last_hour", "last_24_hours", etc.
    """
    #   Replace this with your actual alert history retrieval logic
    return "Alert history retrieval not implemented yet."

if __name__ == "__main__":
    create_table()  #   create table if it does not exist.
    while True:
        log_system_metrics()
        time.sleep(60)  #   Log every 60 seconds
