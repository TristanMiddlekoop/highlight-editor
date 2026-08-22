import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from client_manager import list_clients, load_client, get_client_reports
from report_generator import generate_monthly_report


SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = os.environ.get('TM_EMAIL', 'tmiddlekoop@gmail.com')
SENDER_PASSWORD = os.environ.get('TM_EMAIL_PASSWORD', '')


def send_report_email(client_id, report_path, month=None, year=None):
    config = load_client(client_id)
    if not config:
        print('❌ Client not found: ' + client_id)
        return False

    client_email = config.get('contact_email', '')
    if not client_email:
        print('⚠️  No email on file for: ' + config['client_name'])
        return False

    now = datetime.now()
    if not month:
        month = now.month
    if not year:
        year = now.year

    month_name = datetime(year, month, 1).strftime('%B %Y')
    client_name = config['client_name']
    team_name = config['team_name']

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = client_email
    msg['Subject'] = f'HighlightOS Monthly Report — {team_name} — {month_name}'

    body = f"""Hi {client_name},

Please find attached your HighlightOS monthly report for {month_name}.

Here's a quick summary of what we produced this month for {team_name}:

We've been working hard to make sure your team's highlights are reaching your audience consistently. Your full breakdown is in the attached report.

As always if you have any feedback or want to adjust anything — posting schedule, clip style, player focus — just reply to this email and we'll take care of it.

Thanks for being part of HighlightOS.

Tristan Middlekoop
TM Ventures
tmventures.io
"""

    msg.attach(MIMEText(body, 'plain'))

    if report_path and os.path.exists(report_path):
        with open(report_path, 'rb') as f:
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(f.read())
            encoders.encode_base64(attachment)
            attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=os.path.basename(report_path)
            )
            msg.attach(attachment)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, client_email, msg.as_string())
        server.quit()
        print('✅ Report emailed to: ' + client_email + ' (' + client_name + ')')
        return True
    except Exception as e:
        print('❌ Email failed for ' + client_name + ': ' + str(e))
        return False


def send_all_monthly_reports(month=None, year=None):
    now = datetime.now()
    if not month:
        month = now.month
    if not year:
        year = now.year

    month_name = datetime(year, month, 1).strftime('%B %Y')
    print('========================================')
    print('   TM VENTURES — MONTHLY REPORT EMAILER')
    print('========================================')
    print('Sending ' + month_name + ' reports to all active clients...\n')

    clients = list_clients()
    sent = 0
    failed = 0

    for client in clients:
        if not client.get('active'):
            continue

        client_id = client['client_id']
        print('📊 Generating report for: ' + client['client_name'])

        report_path = generate_monthly_report(client_id, month, year)

        if report_path:
            success = send_report_email(client_id, report_path, month, year)
            if success:
                sent += 1
            else:
                failed += 1
        else:
            print('❌ Could not generate report for: ' + client['client_name'])
            failed += 1

    print('\n========================================')
    print('✅ Reports sent: ' + str(sent))
    if failed:
        print('❌ Failed: ' + str(failed))
    print('========================================')


def add_client_email(client_id, email):
    from client_manager import save_client
    config = load_client(client_id)
    if not config:
        return False
    config['contact_email'] = email
    save_client(client_id, config)
    print('✅ Email added for: ' + config['client_name'] + ' → ' + email)
    return True


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == 'add-email' and len(sys.argv) > 3:
            add_client_email(sys.argv[2], sys.argv[3])
        elif sys.argv[1] == 'send' and len(sys.argv) > 2:
            config = load_client(sys.argv[2])
            if config:
                reports_dir = get_client_reports(sys.argv[2])
                now = datetime.now()
                report_filename = 'report_' + str(now.year) + '_' + str(now.month).zfill(2) + '.txt'
                report_path = os.path.join(reports_dir, report_filename)
                send_report_email(sys.argv[2], report_path)
        else:
            send_all_monthly_reports()
    else:
        send_all_monthly_reports()