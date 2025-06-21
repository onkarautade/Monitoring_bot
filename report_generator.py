# -*- coding: utf-8 -*-

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime, timedelta
import os

DB_PATH = "/home/adm_onkar/Monitoring_script/logs/monitoring_data.db"
REPORT_DIR = "/home/adm_onkar/Monitoring_script/report"
os.makedirs(REPORT_DIR, exist_ok=True)

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
    generated_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    plt.figtext(0.99, 0.01,
                f"Generated: {generated_time}\nPeriod: {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}",
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
    generated_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    plt.figtext(0.99, 0.01,
                f"Generated: {generated_time}\nPeriod: {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}",
                horizontalalignment='right', fontsize=8)
    pdf.savefig()
    plt.close()

def add_summary_page(df, pdf, start, end):
    df_google = df[df['host'] == 'Google DNS'].copy()
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

    plt.figure(figsize=(10, 6))
    plt.axis('off')
    summary_text = f"""
? Network Report Summary

? Time Period: {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}
? Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

? Uptime: {uptime_pct:.2f}%
? Downtime: {downtime_pct:.2f}%

? Average Latency: {avg_latency:.2f} ms
? Average Jitter: {avg_jitter:.2f} ms
? Average Packet Loss: {avg_packet_loss:.2f}%
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

    df = fetch_network_data(start.strftime('%Y-%m-%d %H:%M:%S'), end.strftime('%Y-%m-%d %H:%M:%S'))
    if df.empty:
        return None

    filename = f"network_report_{start.strftime('%Y%m%d_%H%M%S')}.pdf"
    report_path = os.path.join(REPORT_DIR, filename)

    with PdfPages(report_path) as pdf:
        add_summary_page(df, pdf, start, end)
        for metric in ['latency', 'jitter', 'packet_loss']:
            plot_metric(df, metric, pdf, start, end)
        plot_availability(df, pdf, start, end)

    return report_path

def purge_old_reports():
    now = datetime.now()
    for fname in os.listdir(REPORT_DIR):
        fpath = os.path.join(REPORT_DIR, fname)
        if os.path.isfile(fpath):
            created = datetime.fromtimestamp(os.path.getctime(fpath))
            if (now - created).total_seconds() > 86400:
                os.remove(fpath)
