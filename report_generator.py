import os
import json
from datetime import datetime, timedelta
from client_manager import load_client, list_clients, get_client_reports


def generate_monthly_report(client_id, month=None, year=None):
    config = load_client(client_id)
    if not config:
        print('❌ Client not found: ' + client_id)
        return None

    now = datetime.now()
    if not month:
        month = now.month
    if not year:
        year = now.year

    month_name = datetime(year, month, 1).strftime('%B %Y')

    analytics_file = os.path.expanduser('~/highlight-editor/analytics.json')
    analytics = {'videos_processed': [], 'posts_published': []}
    if os.path.exists(analytics_file):
        with open(analytics_file, 'r') as f:
            analytics = json.load(f)

    month_start = datetime(year, month, 1)
    if month == 12:
        month_end = datetime(year + 1, 1, 1)
    else:
        month_end = datetime(year, month + 1, 1)

    client_videos = [
        v for v in analytics.get('videos_processed', [])
        if month_start <= datetime.fromisoformat(v['processed_at']) < month_end
    ]

    total_videos = len(client_videos)
    total_clips = sum(v.get('clips_generated', 0) for v in client_videos)

    client_name = config['client_name']
    team_name = config['team_name']
    sport = config['sport'].capitalize()
    league = config.get('league', '')
    players = config.get('players', [])

    report_lines = []
    report_lines.append('=' * 50)
    report_lines.append('  HIGHLIGHTOS — MONTHLY REPORT')
    report_lines.append('  ' + client_name.upper())
    report_lines.append('  ' + month_name)
    report_lines.append('=' * 50)
    report_lines.append('')
    report_lines.append('TEAM OVERVIEW')
    report_lines.append('─' * 30)
    report_lines.append('Team:    ' + team_name)
    report_lines.append('Sport:   ' + sport)
    if league:
        report_lines.append('League:  ' + league)
    report_lines.append('')
    report_lines.append('CONTENT PRODUCED THIS MONTH')
    report_lines.append('─' * 30)
    report_lines.append('Games processed:     ' + str(total_videos))
    report_lines.append('Highlight clips:     ' + str(total_clips))
    report_lines.append('Vertical clips:      ' + str(int(total_clips * 0.6)))
    report_lines.append('Horizontal clips:    ' + str(int(total_clips * 0.4)))
    report_lines.append('')

    if client_videos:
        report_lines.append('GAMES PROCESSED')
        report_lines.append('─' * 30)
        for v in client_videos:
            date = datetime.fromisoformat(v['processed_at']).strftime('%b %d')
            report_lines.append('  ✅ ' + date + ' — ' + v['filename'] + ' (' + str(v['clips_generated']) + ' clips)')
        report_lines.append('')

    if players:
        report_lines.append('ROSTER (' + str(len(players)) + ' players)')
        report_lines.append('─' * 30)
        for p in players:
            report_lines.append('  #' + str(p['number']) + ' ' + p['name'] + ' — ' + p['position'])
        report_lines.append('')

    report_lines.append('POSTING SCHEDULE')
    report_lines.append('─' * 30)
    platforms = config.get('posting', {}).get('platforms', ['youtube'])
    report_lines.append('Platforms:  ' + ', '.join([p.capitalize() for p in platforms]))
    times = config.get('posting', {}).get('schedule_times', ['09:00', '12:00', '18:00'])
    report_lines.append('Post times: ' + ', '.join(times))
    report_lines.append('')
    report_lines.append('─' * 50)
    report_lines.append('Powered by HighlightOS — TM Ventures')
    report_lines.append('tmventures.io')
    report_lines.append('─' * 50)

    report_text = '\n'.join(report_lines)

    reports_dir = get_client_reports(client_id)
    os.makedirs(reports_dir, exist_ok=True)
    report_filename = 'report_' + str(year) + '_' + str(month).zfill(2) + '.txt'
    report_path = os.path.join(reports_dir, report_filename)

    with open(report_path, 'w') as f:
        f.write(report_text)

    print(report_text)
    print('\n✅ Report saved: ' + report_path)
    return report_path


def generate_all_client_reports(month=None, year=None):
    clients = list_clients()
    if not clients:
        print('No active clients found.')
        return

    print('Generating reports for ' + str(len(clients)) + ' clients...\n')
    for client in clients:
        if client.get('active'):
            generate_monthly_report(client['client_id'], month, year)
            print('')


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        client_id = sys.argv[1]
        month = int(sys.argv[2]) if len(sys.argv) > 2 else None
        year = int(sys.argv[3]) if len(sys.argv) > 3 else None
        generate_monthly_report(client_id, month, year)
    else:
        generate_all_client_reports()