##Raspberry Pi Monitoring System
A secure Telegram-based monitoring system that logs:
-Network uptimeSystem metrics (CPU, RAM, Temp)
-Daily PDF Reports
-Remote Commands (Expert Mode)
#Features
-SQLite-backed logging
-PDF Report generation
-Telegram Bot alerts
-Expert mode with command filter
-SSH GitHub backups
##Note on Development & Future Improvements

This project was developed with the assistance of large language models and code-completion tools, including ChatGPT, Gemini, and Copilot. As such, it represents an exploration of what can be accomplished with AI-assisted development.

Please feel free to reach out with any suggestions for improvements in this script. In the spirit of open collaboration, here are a few technical points to consider for future development:
--Implement a Database Pruning Mechanism: The current system does not have a function to delete old records from the SQLite database. This will cause the database file to grow indefinitely, eventually consuming all available storage on the Raspberry Pi. A periodic cleanup function is highly recommended.

--Refactor the Alerting System: The current in-memory alert list (stored_alerts in system_monitor.py) is not persistent and is cleared after a single retrieval. A more robust solution would be to log all critical alerts to a dedicated, persistent table in the database to ensure an auditable history that survives reboots.

--Centralize Configuration: Configuration parameters such as database paths (DB_PATH) are currently hardcoded in multiple scripts. Consolidating all configurable variables into a single .env file would greatly simplify deployment and maintenance.

--Enhance Expert Mode Security: The subprocess.run(shell=True) call in bot.py is a potential security risk, as it allows for command chaining if not properly sanitized. A more robust approach would be to pass the command and its arguments as a list to subprocess.run() to avoid relying on the shell interpreter.
