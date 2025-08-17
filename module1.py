# module1.py - Network Connectivity Monitoring
import subprocess
import re
import time
import logging
import sqlite3
import datetime
import os

# Configure logging
logging.basicConfig(
    filename='network_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

DB_PATH = "/home/onkar/Monitoring_script/logs/monitoring_data.db"  # Database path

def create_table():
    """Creates the network_logs table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS network_logs (
            timestamp TEXT,
            host TEXT,
            latency REAL,
            jitter REAL,
            packet_loss REAL,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def ping_host(host, count=10):
    """Pings a host and returns the average latency, jitter, and packet loss."""
    try:
        # Run the ping command
        result = subprocess.run(['ping', '-c', str(count), host], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Log the full output for debugging
        logging.debug(f"Ping output for {host}: {result.stdout}")
        
        if result.returncode == 0:
            # Extract the latency and packet loss from the output
            output = result.stdout
            packet_loss_match = re.search(r'(\d+)% packet loss', output)
            latency_match = re.search(r'rtt min/avg/max/mdev = (\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)', output)

            if packet_loss_match and latency_match:
                packet_loss = float(packet_loss_match.group(1))
                avg_latency = float(latency_match.group(2))

                # For jitter, we can calculate it as the difference between the max and min latency values
                min_latency = float(latency_match.group(1))
                max_latency = float(latency_match.group(3))
                jitter = max_latency - min_latency

                return avg_latency, jitter, packet_loss
            else:
                logging.warning(f"Could not parse latency or packet loss for {host}.")
                return None
        else:
            logging.error(f"Ping failed for {host}: {result.stderr}")
            return None

    except Exception as e:
        logging.error(f"Error pinging {host}: {str(e)}")
        return None



def save_to_db(host, latency, jitter, packet_loss, status):
    """Saves network data to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO network_logs (timestamp, host, latency, jitter, packet_loss, status) VALUES (?, ?, ?, ?, ?, ?)",
        (timestamp, host, latency, jitter, packet_loss, status)
    )
    conn.commit()
    conn.close()

def main():
    create_table()  # Create table before any other operations
    hosts = {
        'Google DNS': '8.8.8.8',
        'Cloudflare DNS': '1.1.1.1',
        'Local Gateway': '192.168.1.1'  # Replace with your actual gateway IP
    }

    results = {}
    for name, ip in hosts.items():
        result = ping_host(ip)
        if result:
            results[name] = result
            logging.info(f"{name} ({ip}) - Avg Latency: {result[0]:.2f} ms, Jitter: {result[1]:.2f} ms, Packet Loss: {result[2]:.2f}%")
            save_to_db(name, result[0], result[1], result[2], "UP")
        else:
            results[name] = None
            logging.warning(f"Failed to retrieve data for {name} ({ip}).")
            save_to_db(name, None, None, None, "DOWN")

    gateway_status = results['Local Gateway'] is not None
    dns_status = any(results[dns] is not None for dns in ['Google DNS', 'Cloudflare DNS'])

    if gateway_status and dns_status:
        logging.info("Network Status: Internet is available.")
    elif gateway_status and not dns_status:
        logging.warning("Network Status: Internet issue detected.")
    else:
        logging.error("Network Status: Router issue detected.")
        
def get_network_status():
    """
    Fetch the latest network status from the database instead of re-pinging.
    Returns a dictionary with the most recent data for each host.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    results = {}
    hosts = ['Google DNS', 'Cloudflare DNS', 'Local Gateway']

    for host in hosts:
        cursor.execute(
            "SELECT latency, jitter, packet_loss, status, timestamp FROM network_logs WHERE host = ? ORDER BY timestamp DESC LIMIT 1",
            (host,)
        )
        row = cursor.fetchone()
        
        if row:
            results[host] = {
                "Latency": row[0],
                "Jitter": row[1],
                "Packet Loss": row[2],
                "Status": row[3],
                "Last Checked": row[4]
            }
        else:
            results[host] = {"Status": "UNKNOWN", "Message": "No data available"}

    conn.close()
    return results


if __name__ == "__main__":
    while True:
        main()
        time.sleep(180)  # Check every 3 minutes
