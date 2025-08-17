# -*- coding: utf-8 -*-

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime, timedelta
import os

DB_PATH = "/home/onkar/Monitoring_script/logs/monitoring_data.db"
REPORT_DIR = "/home/onkar/Monitoring_script/report"
os.makedirs(REPORT_DIR, exist_ok=True)

SYSTEM_THRESHOLDS = {
    'cpu_usage': 80.0,
    'ram_usage': 80.0,
    'storage_usage': 70.0,
    'temperature': 60.0
}

def fetch_network_data(start_time, end_time):
    conn = sqlite3.connect(DB_PATH)
    query = '''
        SELECT timestamp, host, latency, jitter, packet_loss, status FROM network_logs
        WHERE timestamp BETWEEN ? AND ?
        ORDER BY timestamp ASC
    '''
    df = pd.read_sql_query(query, conn, params=(start_time, end_time), parse_dates=['timestamp'])
    conn.close()
    return df

def fetch_system_util_data(start_time, end_time):
    conn = sqlite3.connect(DB_PATH)
    query = '''
        SELECT timestamp, 
               cpu_temp AS temperature, 
               cpu_usage, 
               ram_usage, 
               storage_usage 
        FROM system_resources
        WHERE timestamp BETWEEN ? AND ?
        ORDER BY timestamp ASC
    '''
    df = pd.read_sql_query(query, conn, params=(start_time, end_time), parse_dates=['timestamp'])
    conn.close()
    return df


def plot_metric(df, metric, pdf, start, end):
    plt.figure(figsize=(10, 5))
    for host in df['host'].unique():
        subset = df[df['host'] == host]
        plt.plot(subset['timestamp'], subset[metric], label=host)
    plt.title(f"{metric.title()} Over Time")
    plt.xlabel("Time")
    plt.ylabel(metric.title())
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.legend()
    plt.figtext(0.99, 0.05,
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nPeriod: {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}\n\n",
                horizontalalignment='right', fontsize=8)
    pdf.savefig()
    plt.close()

def plot_availability(df, pdf, start, end):
    df_status = df[df['host'] == 'Google DNS'].copy()
    df_status['availability'] = df_status['status'].apply(lambda x: 1 if x == 'UP' else 0)
    plt.figure(figsize=(10, 3))
    plt.plot(df_status['timestamp'], df_status['availability'], drawstyle='steps-post', marker='o', color='green')
    plt.title("Internet Availability")
    plt.xlabel("Time")
    plt.ylabel("Availability")
    plt.xticks(rotation=45)
    plt.ylim(-0.1, 1.1)
    plt.grid(True)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.figtext(0.99, 0.05,
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nPeriod: {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}\n\n",
                horizontalalignment='right', fontsize=8)
    pdf.savefig()
    plt.close()

def plot_system_util(df, metric, pdf, start, end):
    plt.figure(figsize=(10, 5))
    plt.plot(df['timestamp'], df[metric], label=metric, color='orange')
    if metric in SYSTEM_THRESHOLDS:
        plt.axhline(y=SYSTEM_THRESHOLDS[metric], color='red', linestyle='--', label=f"Threshold {SYSTEM_THRESHOLDS[metric]}")
    plt.title(f"System {metric.replace('_', ' ').title()} Over Time")
    plt.xlabel("Time")
    plt.ylabel(metric.replace('_', ' ').title())
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.legend()
    plt.figtext(0.99, 0.05,
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nPeriod: {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}\n\n",
                horizontalalignment='right', fontsize=8)
    pdf.savefig()
    plt.close()

def classify_downtime(df):
    df_pivot = df.pivot(index='timestamp', columns='host', values='status').fillna('DOWN')
    no_electricity = df_pivot.apply(lambda row: all(row[h] == 'DOWN' for h in ['Google DNS', 'Cloudflare DNS', 'Local Gateway']), axis=1)
    no_internet = df_pivot.apply(lambda row: (row['Google DNS'] == 'DOWN' and row['Cloudflare DNS'] == 'DOWN') and row['Local Gateway'] == 'UP', axis=1)
    return no_electricity.sum(), no_internet.sum(), df_pivot.shape[0]

def summarize_system_util(df):
    return {
        'avg_cpu': df['cpu_usage'].mean(),
        'avg_ram': df['ram_usage'].mean(),
        'avg_storage': df['storage_usage'].mean(),
        'avg_temp': df['temperature'].mean()
    }

def add_summary_page(df_net, df_sys, pdf, start, end):
    df_google = df_net[df_net['host'] == 'Google DNS'].copy()
    total_entries = len(df_google)
    if total_entries == 0:
        uptime_pct = 0
        downtime_pct = 0
    else:
        up_count = df_google[df_google['status'] == 'UP'].shape[0]
        uptime_pct = (up_count / total_entries) * 100
        downtime_pct = 100 - uptime_pct

    avg_latency = df_google['latency'].mean()
    avg_jitter = df_google['jitter'].mean()
    avg_packet_loss = df_google['packet_loss'].mean()

    no_elec_count, no_internet_count, total_net = classify_downtime(df_net)
    no_elec_pct = (no_elec_count / total_net) * 100 if total_net else 0
    no_internet_pct = (no_internet_count / total_net) * 100 if total_net else 0

    system_stats = summarize_system_util(df_sys) if not df_sys.empty else {'avg_cpu': 0, 'avg_ram': 0, 'avg_storage': 0, 'avg_temp': 0}

    plt.figure(figsize=(10, 6))
    plt.axis('off')
    summary_text = f"""
📊 Network & System Report Summary

🕒 Time Period: {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}
📅 Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📶 Internet Uptime: {uptime_pct:.2f}%
📉 Internet Downtime: {downtime_pct:.2f}%
⚠️ No Electricity: {no_elec_pct:.2f}%
📡 Internet Down (Electricity Present): {no_internet_pct:.2f}%

🧠 Avg CPU Usage: {system_stats['avg_cpu']:.2f}%
🧠 Avg RAM Usage: {system_stats['avg_ram']:.2f}%
💾 Avg Storage Usage: {system_stats['avg_storage']:.2f}%
🌡️ Avg Temperature: {system_stats['avg_temp']:.2f}°C
    """
    plt.text(0, 0.5, summary_text, fontsize=12, va='center')
    pdf.savefig()
    plt.close()

def generate_report(time_range='today', custom_date=None):
    now = datetime.now()
    if time_range == 'last_hour':
        start = now - timedelta(hours=1)
        end = now
    elif time_range == 'last_24_hours':
        start = now - timedelta(days=1)
        end = now
    elif time_range == 'today':
        start = datetime(now.year, now.month, now.day)
        end = now
    elif time_range == 'yesterday':
        start = datetime(now.year, now.month, now.day) - timedelta(days=1)
        end = datetime(now.year, now.month, now.day)
    elif time_range == 'custom' and custom_date:
        try:
            start = datetime.strptime(custom_date, '%Y-%m-%d')
            end = start + timedelta(days=1)
        except ValueError:
            raise ValueError("Invalid custom date format. Use YYYY-MM-DD.")
    else:
        raise ValueError("Invalid time_range or missing custom_date.")

    df_net = fetch_network_data(start.strftime('%Y-%m-%d %H:%M:%S'), end.strftime('%Y-%m-%d %H:%M:%S'))
    df_sys = fetch_system_util_data(start.strftime('%Y-%m-%d %H:%M:%S'), end.strftime('%Y-%m-%d %H:%M:%S'))

    if df_net.empty and df_sys.empty:
        return None

    filename = f"network_report_{start.strftime('%Y%m%d_%H%M%S')}.pdf"
    report_path = os.path.join(REPORT_DIR, filename)

    with PdfPages(report_path) as pdf:
        add_summary_page(df_net, df_sys, pdf, start, end)

        if not df_net.empty:
            for metric in ['latency', 'jitter', 'packet_loss']:
                plot_metric(df_net, metric, pdf, start, end)
            plot_availability(df_net, pdf, start, end)

        if not df_sys.empty:
            for metric in ['cpu_usage', 'ram_usage', 'storage_usage', 'temperature']:
                plot_system_util(df_sys, metric, pdf, start, end)

    return report_path

def purge_old_reports():
    now = datetime.now()
    for fname in os.listdir(REPORT_DIR):
        fpath = os.path.join(REPORT_DIR, fname)
        if os.path.isfile(fpath):
            created = datetime.fromtimestamp(os.path.getctime(fpath))
            if (now - created).total_seconds() > 86400:
                os.remove(fpath)
