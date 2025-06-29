# -*- coding: utf-8 -*-
# bot_clean.py - Unified and Clean Bot with Full Functionality Including Expert Mode

import telebot
import subprocess
import logging
import os
import time
import sys
import threading
from dotenv import load_dotenv
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from system_monitor import get_system_status, get_stored_alerts, get_private_ip, get_public_ip
from module1 import get_network_status
from command_filter import is_safe_command, SAFE_COMMANDS
from report_generator import generate_report, purge_old_reports

# --- Load and Setup ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing in the .env file!")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
ALLOWED_CHAT_ID = {710548578, 5887269201, 1148184296}
UPTIME_ALERT_THRESHOLD = 95

logging.basicConfig(level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bot_debug.log"), logging.StreamHandler(sys.stdout)])

# --- Access Control ---
def is_allowed_user(entity):
    return entity.chat.id in ALLOWED_CHAT_ID

# --- Bot UI ---
@bot.message_handler(commands=['start'])
def welcome(message):
    if not is_allowed_user(message):
        return bot.send_message(message.chat.id, "Access Denied.")

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📊 Report Generation", callback_data="report_menu"),
        InlineKeyboardButton("💻 System Status", callback_data="system_status"),
        InlineKeyboardButton("🌐 Network Status", callback_data="network_status"),
        InlineKeyboardButton("📡 IP Config", callback_data="ip_config"),
        InlineKeyboardButton("🚨 Alerts", callback_data="alerts"),
        InlineKeyboardButton("🛠 R2-Utilities", callback_data="r2_utilities_menu")
    )
    bot.send_message(message.chat.id, "<b>Welcome to the Monitoring Bot!</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    if not is_allowed_user(call.message):
        return bot.send_message(call.message.chat.id, "Access Denied.")
    data = call.data
    if data == "system_status": show_system_status(call.message)
    elif data == "network_status": show_network_status(call.message)
    elif data == "ip_config": show_ip_config(call.message)
    elif data == "report_menu": show_report_menu(call.message)
    elif data == "alerts": show_alerts(call.message)
    elif data.startswith("report_"): generate_and_send_report(call.message, data)
    elif data == "r2_utilities_menu": show_utilities_menu(call.message)
    elif data == "r2_reboot": reboot_pi(call.message)
    elif data == "r2_ping_camera": ping_camera(call.message)
    elif data == "expert_mode_shell": expert_mode_shell_handler(call)

@bot.message_handler(func=lambda m: True)
def handle_unknown(m):
    bot.send_message(m.chat.id, "Unknown command. Use /start or /help.")

# --- Core Functions ---
def show_system_status(message):
    try:
        bot.send_message(message.chat.id, f"<pre>{get_system_status()}</pre>")
    except Exception as e:
        logging.error(f"System status error: {e}")
        bot.send_message(message.chat.id, "Failed to fetch system status.")

def show_network_status(message):
    try:
        net = get_network_status()
        text = "<b>Network Status:</b>"
        for k, v in net.items():
            text += (
                f"\n\n<b>{k}</b>\n"
                f"• Latency: {v['Latency']} ms\n"
                f"• Jitter: {v['Jitter']} ms\n"
                f"• Packet Loss: {v['Packet Loss']}%\n"
                f"• Status: {v['Status']}\n"
                f"• Checked: {v['Last Checked']}"
            )
        bot.send_message(message.chat.id, text, parse_mode="HTML")
    except Exception as e:
        logging.exception("Network status error")
        bot.send_message(message.chat.id, f"❌ Error: {str(e)}")

def show_ip_config(message):
    try:
        pub_ip = get_public_ip()
        priv_ip = get_private_ip()
        priv_ip_str = "\n".join(priv_ip) if isinstance(priv_ip, list) else str(priv_ip)

        msg = (
            f"<b>IP Info:</b>\n"
            f"Public: {pub_ip}\n"
            f"Private:\n{priv_ip_str}"
        )
        bot.send_message(message.chat.id, msg, parse_mode="HTML")
    except Exception as e:
        logging.error(f"IP config error: {e}")
        bot.send_message(message.chat.id, f"❌ IP error: {str(e)}")

def show_alerts(message):
    try:
        alerts = get_stored_alerts()
        text = "<b>Alerts:</b><br>" + ("<br>".join(alerts) if alerts else "No critical alerts.")
        bot.send_message(message.chat.id, text)
    except Exception as e:
        logging.error(f"Alerts fetch error: {e}")
        bot.send_message(message.chat.id, "Failed to fetch alerts.")

def show_report_menu(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Last Hour", callback_data="report_last_hour"),
        InlineKeyboardButton("Last 24 Hours", callback_data="report_last_24"),
        InlineKeyboardButton("Today", callback_data="report_today"),
        InlineKeyboardButton("Yesterday", callback_data="report_yesterday"),
        InlineKeyboardButton("Custom Date", callback_data="report_custom")
    )
    bot.send_message(message.chat.id, "<b>Select a report range:</b>", reply_markup=markup)

def generate_and_send_report(message, tag):
    range_map = {
        "report_last_hour": "last_hour",
        "report_last_24": "last_24_hours",
        "report_today": "today",
        "report_yesterday": "yesterday"
    }
    if tag in range_map:
        try:
            path = generate_report(range_map[tag])
            if path:
                with open(path, 'rb') as f:
                    bot.send_document(message.chat.id, f, caption="✅ Report Ready")
            else:
                bot.send_message(message.chat.id, "No data for this range.")
        except Exception as e:
            logging.error(f"Report error: {e}")
            bot.send_message(message.chat.id, "Report generation failed.")
    elif tag == "report_custom":
        bot.send_message(message.chat.id, "Send date in YYYY-MM-DD format:")
        bot.register_next_step_handler(message, get_report_for_date)

def get_report_for_date(message):
    try:
        date = message.text.strip()
        datetime.strptime(date, "%Y-%m-%d")
        path = generate_report("custom", date)
        if path:
            with open(path, 'rb') as f:
                bot.send_document(message.chat.id, f)
        else:
            bot.send_message(message.chat.id, "No data found for that date.")
    except Exception as e:
        logging.error(f"Custom date report error: {e}")
        bot.send_message(message.chat.id, "Invalid date or generation error.")

def show_utilities_menu(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Clear Memory (Reboot)", callback_data="r2_reboot"),
        InlineKeyboardButton("Ping Camera", callback_data="r2_ping_camera"),
        InlineKeyboardButton("🧠 Expert Mode", callback_data="expert_mode_shell")
    )
    bot.send_message(message.chat.id, "<b>R2-Utilities Menu:</b>", reply_markup=markup)

def reboot_pi(message):
    bot.send_message(message.chat.id, "Rebooting Pi...")
    subprocess.run(["sudo", "reboot"], check=False)

def ping_camera(message):
    ip = "192.168.1.2"
    try:
        out = subprocess.run(["ping", "-c", "4", ip], capture_output=True, text=True)
        bot.send_message(message.chat.id, f"<pre>{out.stdout}</pre>")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ping failed: {e}")

def expert_mode_shell_handler(call):
    bot.send_message(call.message.chat.id, "<b>Expert Mode Activated.</b>\nSend a safe shell command:")
    bot.register_next_step_handler(call.message, execute_shell_command)

def execute_shell_command(message):
    if not is_allowed_user(message):
        return bot.send_message(message.chat.id, "Access Denied.")

    cmd = message.text.strip()
    if not is_safe_command(cmd):
        allowed = "\n".join(SAFE_COMMANDS)
        return bot.send_message(
            message.chat.id,
            f"<b>❌ Blocked Command</b>\nAllowed commands:\n<pre>{allowed}</pre>",
            parse_mode="HTML"
        )

    try:
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=10)
        output = result.stdout.strip() or "✅ Command executed, but no output returned."
        
        # Escape unsafe HTML characters for Telegram
        safe_output = output.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Limit to last 4000 characters (Telegram message limit)
        safe_output = safe_output[-4000:]

        bot.send_message(message.chat.id, f"<pre>{safe_output}</pre>", parse_mode="HTML")

    except subprocess.TimeoutExpired:
        bot.send_message(message.chat.id, "❌ Command timed out.")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Error: {str(e)}")


# --- Auto Daily Reports ---
def notify_all(text):
    for uid in ALLOWED_CHAT_ID:
        try:
            bot.send_message(uid, text)
        except:
            pass

def auto_daily_report():
    date_file = ".last_report_date"
    
    def read_last_date():
        if os.path.exists(date_file):
            with open(date_file, "r") as f:
                return f.read().strip()
        return None

    def write_last_date(date_str):
        with open(date_file, "w") as f:
            f.write(date_str)

    while True:
        today_str = datetime.now().date().isoformat()
        last_date = read_last_date()
        
        if last_date != today_str:
            try:
                path = generate_report("yesterday")
                if path:
                    for uid in ALLOWED_CHAT_ID:
                        with open(path, 'rb') as f:
                            bot.send_document(uid, f, caption="📊 Yesterday's Report")
                    notify_all("<b>📈 Report sent automatically.</b>")
                else:
                    notify_all("❌ No data for yesterday.")
                
                purge_old_reports()
                write_last_date(today_str)
            except Exception as e:
                logging.error(f"Auto-report error: {e}")

        time.sleep(900)

# --- Startup ---
def start_bot():
    threading.Thread(target=auto_daily_report, daemon=True).start()
    bot.infinity_polling(timeout=30)

if __name__ == '__main__':
    purge_old_reports()
    start_bot()
