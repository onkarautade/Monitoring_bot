# Raspberry Pi Monitoring System

A secure, Telegram-based monitoring system for **remote administration and reporting**.

## 📋 Logged Data

- **Network uptime**
- **System metrics**: CPU, RAM, Temperature
- **Daily PDF Reports**
- **Remote Commands** (Expert Mode)

## 🚀 Features

- SQLite-backed logging
- PDF report generation
- Telegram Bot alerts
- Expert mode with command filter
- SSH GitHub backups

---

## 🛠 Development & Future Improvements

This project was developed with the assistance of **large language models** and **code-completion tools**, including *ChatGPT*, *Gemini*, and *Copilot*.  
It represents an exploration of what can be accomplished with AI-assisted development.

### 💡 Suggestions for Further Development

1. **Implement a Database Pruning Mechanism**  
   - The current system does not delete old records from the SQLite database.  
   - Without cleanup, the database will grow indefinitely, eventually consuming all available storage on the Raspberry Pi.  
   - **Recommendation**: Implement a periodic cleanup function.

2. **Refactor the Alerting System**  
   - The in-memory alert list (`stored_alerts` in `system_monitor.py`) is cleared after a single retrieval and is not persistent.  
   - **Recommendation**: Log all critical alerts to a persistent table for auditable history across reboots.

3. **Centralize Configuration**  
   - Configuration parameters like `DB_PATH` are hardcoded in multiple scripts.  
   - **Recommendation**: Consolidate all configuration variables into a single `.env` file for easier deployment and maintenance.

4. **Enhance Expert Mode Security**  
   - The `subprocess.run(shell=True)` call in `bot.py` is a potential security risk, as it allows command chaining if not properly sanitized.  
   - **Recommendation**: Pass the command and its arguments as a list to `subprocess.run()` to avoid relying on the shell interpreter.

---

📬 **Feedback Welcome** — Contributions, improvements, and security recommendations are encouraged to make this system more robust and production-ready.
