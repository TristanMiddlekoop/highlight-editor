import os
import time
import subprocess
import sys
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from analytics import track_video_processed
from overlay import apply_overlays_to_folder
from client_manager import load_client, get_client_inbox, get_client_output

WATCH_FOLDER = os.path.expanduser('~/highlight-editor/watch_inbox')
CLIENTS_DIR = os.path.expanduser('~/highlight-editor/clients')
OUTPUT_FOLDER = os.path.expanduser('~/highlight-editor/output')
PROCESSED_FOLDER = os.path.expanduser('~/highlight-editor/watch_processed')
SUPPORTED_FORMATS = {'.mp4', '.mov', '.webm', '.avi', '.mkv'}

os.makedirs(WATCH_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
ENABLE_CAPTIONS = False


def detect_sport(filename):
    filename_lower = filename.lower()
    sport_keywords = {
        'basketball': ['basketball', 'nba', 'wnba', 'hoops', 'bball'],
        'soccer': ['soccer', 'football', 'fifa', 'mls', 'epl'],
        'darts': ['darts', 'pdc', 'bdo', 'oche', 'bullseye', 'checkout', 'premier_darts'],
        'mma': ['mma', 'ufc', 'fight', 'boxing', 'combat'],
        'football': ['nfl', 'american_football', 'gridiron'],
        'hockey': ['hockey', 'nhl', 'ice'],
        'cricket': ['cricket', 'ipl', 'test_match'],
        'tennis': ['tennis', 'wimbledon', 'usopen', 'atp', 'wta'],
        'darts': ['darts', 'pdc', 'bdo', 'oche', 'bullseye', 'checkout']
    }

    for sport, keywords in sport_keywords.items():
        for keyword in keywords:
            if keyword in filename_lower:
                return sport
    return 'basketball'


class VideoHandler(FileSystemEventHandler):
    def __init__(self):
        self.processing = set()

    def on_created(self, event):
        if event.is_directory:
            return

        filepath = event.src_path
        ext = Path(filepath).suffix.lower()

        if ext not in SUPPORTED_FORMATS:
            return

        if filepath in self.processing:
            return

        time.sleep(2)

        if not os.path.exists(filepath):
            return

        self.processing.add(filepath)
        print('\n📥 New video detected: ' + os.path.basename(filepath))
        self.process_video(filepath)
        self.processing.discard(filepath)

    def process_video(self, filepath):
        filename = os.path.basename(filepath)
        sport = detect_sport(filename)

        print('🏃 Auto-processing: ' + filename)
        print('🎯 Sport detected: ' + sport)
        print('⚙️  Running highlight pipeline...')

        try:
            cmd = [
                sys.executable,
                os.path.expanduser('~/highlight-editor/main.py'),
                filepath,
                'both',
                sport,
                '5'
            ]
            if ENABLE_CAPTIONS:
                cmd.extend(['captions', '1.3', '0.88'])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

            if result.returncode == 0:
                print('✅ Pipeline complete for: ' + filename)
                clips_count = result.stdout.count('Saved:')
                track_video_processed(filename, sport, clips_count)
                overlay_config = {
                    'home_team': 'HOME',
                    'away_team': 'AWAY',
                    'home_score': 0,
                    'away_score': 0,
                    'game_time': '00:00',
                    'period': 'Q1',
                    'ticker_text': '',
                    'sport': sport,
                    'hype_score': 75,
                    'team_color': [255, 140, 0],
                    'player_name': '',
                    'stat_line': '',
                    'show_scoreboard': False,
                    'show_lower_third': False,
                    'show_label': True
                }
                print('🎬 Applying broadcast overlay...')
                apply_overlays_to_folder(OUTPUT_FOLDER, overlay_config, recent_only=True)
                print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)

                processed_path = os.path.join(PROCESSED_FOLDER, filename)
                if os.path.exists(filepath):
                    os.rename(filepath, processed_path)
                    print('📦 Moved to processed: ' + processed_path)
                else:
                    print('📦 File already processed')
            else:
                print('❌ Pipeline failed for: ' + filename)
                print(result.stderr[-300:] if len(result.stderr) > 300 else result.stderr)

        except subprocess.TimeoutExpired:
            print('⏱️ Pipeline timed out for: ' + filename)
        except Exception as e:
            print('❌ Error processing ' + filename + ': ' + str(e))

def run_client_watcher():
    print('========================================')
    print('   TM VENTURES — CLIENT PIPELINE WATCHER')
    print('========================================')
    
    observers = []
    active_clients = []
    
    if os.path.exists(CLIENTS_DIR):
        for client_id in os.listdir(CLIENTS_DIR):
            client_config = load_client(client_id)
            if client_config and client_config.get('active'):
                inbox = get_client_inbox(client_id)
                os.makedirs(inbox, exist_ok=True)
                
                handler = VideoHandler()
                handler.client_id = client_id
                handler.client_config = client_config
                
                observer = Observer()
                observer.schedule(handler, inbox, recursive=False)
                observer.start()
                observers.append(observer)
                active_clients.append(client_config['client_name'])
                print('👤 Watching: ' + client_config['client_name'] + ' → ' + inbox)
    
    if not active_clients:
        print('⚠️  No active clients found. Add clients via client_manager.py')
    else:
        print('\n✅ Watching ' + str(len(active_clients)) + ' client inboxes')
    
    print('Press Ctrl+C to stop.')
    print('========================================\n')
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for observer in observers:
            observer.stop()
        print('\n⛔ Client watcher stopped.')
    
    for observer in observers:
        observer.join()
def run_watcher():
    print('========================================')
    print('   TM VENTURES — AUTO PIPELINE WATCHER')
    print('========================================')
    print('📁 Watching folder: ' + WATCH_FOLDER)
    print('📤 Output folder: ' + OUTPUT_FOLDER)
    print('📦 Processed folder: ' + PROCESSED_FOLDER)
    print('')
    print('Drop any sports video into the watch folder.')
    print('The pipeline will run automatically.')
    print('Sport is detected from the filename.')
    print('e.g. nba_game.mp4 → basketball preset')
    print('e.g. ufc_fight.mp4 → mma preset')
    print('')
    print('Press Ctrl+C to stop watching.')
    print('========================================\n')

    event_handler = VideoHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_FOLDER, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print('\n⛔ Watcher stopped.')

    observer.join()


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'clients':
        run_client_watcher()
    else:
        run_watcher()