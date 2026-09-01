import os
import time
import schedule
from datetime import datetime
from email_sender import send_all_monthly_reports
from report_generator import generate_all_client_reports


def run_monthly_reports():
    now = datetime.now()
    print('========================================')
    print('   TM VENTURES — MONTHLY REPORT SCHEDULER')
    print('========================================')
    print('Running monthly reports for: ' + now.strftime('%B %Y'))
    print('Triggered at: ' + now.strftime('%Y-%m-%d %H:%M:%S'))
    prev_month = now.month - 1 if now.month > 1 else 12
    prev_year = now.year if now.month > 1 else now.year - 1
    print('Generating reports for: ' + datetime(prev_year, prev_month, 1).strftime('%B %Y'))
    send_all_monthly_reports(month=prev_month, year=prev_year)


def check_if_month_start():
    now = datetime.now()
    if now.day == 1:
        print('📅 First of the month — running monthly reports...')
        run_monthly_reports()


def run_scheduler():
    print('========================================')
    print('   TM VENTURES — MONTHLY SCHEDULER')
    print('========================================')
    print('Scheduler running...')
    print('Monthly reports will send on the 1st of each month at 9:00 AM')
    print('========================================\n')
    schedule.every().day.at('09:00').do(check_if_month_start)
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print('\n⛔ Scheduler stopped.')


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'now':
        run_monthly_reports()
    else:
        run_scheduler()
