# test_report_generator.py
from report_generator import generate_report, purge_old_reports
from datetime import datetime, timedelta


def test_all_time_ranges():
    print("Testing Last Hour Report...")
    path = generate_report('last_hour')
    print("? Last Hour:", path if path else "No data")

    print("Testing Last 24 Hours Report...")
    path = generate_report('last_24_hours')
    print("? Last 24 Hours:", path if path else "No data")

    print("Testing Today Report...")
    path = generate_report('today')
    print("? Today:", path if path else "No data")

    print("Testing Yesterday Report...")
    path = generate_report('yesterday')
    print("? Yesterday:", path if path else "No data")

    print("Testing Custom Date Report (Example: yesterday)...")
    custom_date = (datetime.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')
    path = generate_report('custom', custom_date)
    print(f"? Custom ({custom_date}):", path if path else "No data")

def test_purge():
    print("Purging old reports...")
    purge_old_reports()
    print("? Purge complete.")

if __name__ == "__main__":
    test_all_time_ranges()
    test_purge()
