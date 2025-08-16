# Raspberry Pi Monitoring System

A secure **Telegram-based monitoring system** that logs:

- **Network uptime**
- **System metrics** (CPU, RAM, Temperature)
- **Daily PDF Reports**
- **Remote Commands** (Expert Mode)

---

## 🚀 Features

- SQLite-backed logging
- PDF report generation
- Telegram Bot alerts
- Expert mode with command filter
- SSH GitHub backups

---

## 📦 Applications & Use Cases

This script provides a comprehensive solution for managing and monitoring a **headless Raspberry Pi**.  
Its design enables a wide range of practical applications:

1. **Remote Monitoring**  
   Remotely check system vitals like CPU temperature, RAM usage, and storage to prevent issues such as overheating or disk space exhaustion.

2. **Network Diagnostics**  
   Analyze network performance with metrics like latency, jitter, and packet loss to diagnose connectivity problems.

3. **Automated Reports**  
   Automatically generate and send daily PDF reports for long-term performance tracking and historical record-keeping.

4. **Secure Remote Administration**  
   Execute a predefined list of safe shell commands remotely to perform quick diagnostics and administration without compromising security.

5. **IP Information**  
   Easily retrieve the public and private IP addresses of the Raspberry Pi for simplified network troubleshooting.

6. **Proactive Alerts**  
   Receive real-time alerts for critical issues like high CPU temperature or low storage, helping to prevent system failures.

7. **Device Management**  
   Use the bot to manage specific embedded devices like a Raspberry Pi-based camera system or a home automation hub.

---

## 🛠 Development & Future Improvements

This project was developed with the assistance of **large language models** and **code-completion tools**, including *ChatGPT*, *Gemini*, and *Copilot*.  
It represents an exploration of what can be accomplished with **AI-assisted development**.

### 💡 Suggestions for Further Development

1. **Implement a Database Pruning Mechanism**  
   - The current system does not delete old records from the SQLite database.  
   - Without cleanup, the database will grow indefinitely, eventually consuming all available storage on the Raspberry Pi.  
   - **Recommendation:** Implement a periodic cleanup function.

2. **Refactor the Alerting System**  
   - The in-memory alert list (`stored_alerts` in `system_monitor.py`) is cleared after a single retrieval and is not persistent.  
   - **Recommendation:** Log all critical alerts to a persistent table for auditable history across reboots.

3. **Centralize Configuration**  
   - Configuration parameters like `DB_PATH` are hardcoded in multiple scripts.  
   - **Recommendation:** Consolidate all configuration variables into a single `.env` file for easier deployment and maintenance.

4. **Enhance Expert Mode Security**  
   - The `subprocess.run(shell=True)` call in `bot.py` is a potential security risk, as it allows command chaining if not properly sanitized.  
   - **Recommendation:** Pass the command and its arguments as a list to `subprocess.run()` to avoid relying on the shell interpreter.

---

📬 **Feedback Welcome** — Contributions, improvements, and security recommendations are encouraged to make this system more robust and production-ready.
