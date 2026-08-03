import os
import subprocess
import json
import glob

WATCH_INBOX = os.path.expanduser('~/highlight-editor/watch_inbox')
SOURCER_LOG = os.path.expanduser('~/highlight-editor/sourcer_log.json')

SPORT_SEARCH_TERMS = {
    'basketball': {
        'leagues': ['NBA', 'WNBA', 'NCAA Basketball'],
        'search_templates': ['{league} highlights today', '{league} best plays', '{league} top moments']
    },
    'soccer': {
        'leagues': ['Premier League', 'La Liga', 'Champions League', 'MLS'],
        'search_templates': ['{league} short highlights', '{league} best goals', '{league} match highlights']
    },
    'mma': {
        'leagues': ['UFC', 'Bellator', 'PFL'],
        'search_templates': ['{league} short highlights', '{league} knockouts', '{league} best fights']
    },
    'darts': {
        'leagues': ['PDC', 'Premier League Darts', 'World Darts Championship'],
        'search_templates': ['{league} short highlights', '{league} 180s checkouts short', '{league} best moments']
    },
    'cricket': {
        'leagues': ['IPL', 'Test Cricket', 'T20 World Cup'],
        'search_templates': ['{league} short highlights', '{league} best sixes', '{league} match highlights']
    },
    'tennis': {
        'leagues': ['Wimbledon', 'US Open', 'Australian Open', 'ATP'],
        'search_templates': ['{league} short highlights', '{league} best points', '{league} match highlights']
    },
    'football': {
        'leagues': ['NFL', 'College Football'],
        'search_templates': ['{league} short highlights', '{league} best plays', '{league} touchdowns']
    },
    'hockey': {
        'leagues': ['NHL'],
        'search_templates': ['{league} short highlights', '{league} best goals', '{league} top plays']
    }
}

def load_sourcer_log():
    if os.path.exists(SOURCER_LOG):
        with open(SOURCER_LOG, 'r') as f:
            return json.load(f)
    return {'downloaded': []}

def save_sourcer_log(log):
    with open(SOURCER_LOG, 'w') as f:
        json.dump(log, f, indent=2)

def search_and_download(sport, league=None, max_videos=2, max_size_mb=150):
    print('========================================')
    print('   TM VENTURES - CONTENT SOURCER')
    print('========================================')
    if sport not in SPORT_SEARCH_TERMS:
        print('Sport not supported: ' + sport)
        return []
    sport_config = SPORT_SEARCH_TERMS[sport]
    if league:
        leagues_to_search = [league]
    else:
        leagues_to_search = sport_config['leagues'][:2]
    log = load_sourcer_log()
    downloaded_files = []

    for search_league in leagues_to_search:
        template = sport_config['search_templates'][0]
        search_query = template.replace('{league}', search_league)
        print('Searching: ' + search_query)

        prefix = sport + '_' + search_league.lower().replace(' ', '_')
        output_path = os.path.join(WATCH_INBOX, prefix + '_%(id)s.%(ext)s')

        before_files = set(glob.glob(os.path.join(WATCH_INBOX, '*.mp4')) + glob.glob(os.path.join(WATCH_INBOX, '*.webm')))

        cmd = [
            'yt-dlp',
            'ytsearch' + str(max_videos) + ':' + search_query,
            '-o', output_path,
            '--max-filesize', str(max_size_mb) + 'M',
            '-f', 'best[height<=720]',
            '--no-playlist',
            '--ignore-errors'
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            after_files = set(glob.glob(os.path.join(WATCH_INBOX, '*.mp4')) + glob.glob(os.path.join(WATCH_INBOX, '*.webm')))
            new_files = after_files - before_files

            for filepath in new_files:
                filename = os.path.basename(filepath)
                if filename not in log['downloaded']:
                    log['downloaded'].append(filename)
                    downloaded_files.append(filepath)
                    print('Downloaded: ' + filename)

            if not new_files:
                print('No new files downloaded for: ' + search_query)
                if result.stderr:
                    print('Error: ' + result.stderr[:200])

        except Exception as e:
            print('Error: ' + str(e))

    save_sourcer_log(log)
    print('Downloaded ' + str(len(downloaded_files)) + ' new videos to watch inbox')
    print('The watcher will process them automatically if running.')
    print('========================================')
    return downloaded_files

def list_available_sports():
    print('AVAILABLE SPORTS AND LEAGUES:')
    for sport, config in SPORT_SEARCH_TERMS.items():
        print(sport.upper() + ': ' + ', '.join(config['leagues']))

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: python3 content_sourcer.py <sport> [league] [max_videos]')
        list_available_sports()
        sys.exit(0)
    sport = sys.argv[1].lower()
    league = sys.argv[2] if len(sys.argv) > 2 else None
    max_videos = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    search_and_download(sport, league, max_videos)
