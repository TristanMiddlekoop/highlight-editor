import os
import time
import subprocess
import sys
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_FOLDER = os.path.expanduser('~/highlight-editor/watch_inbox')
OUTPUT_FOLDER = os.path.expanduser('~/highlight-editor/output')
PROCESSED_FOLDER = os.path.expanduser('~/highlight-editor/watch_processed')
SUPPORTED_FORMATS = {'.mp4', '.mov', '.webm', '.avi', '.mkv'}

os.makedirs(WATCH_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)


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
            result = subprocess.run([
                sys.executable,
                os.path.expanduser('~/highlight-editor/main.py'),
                filepath,
                'both',
                sport,
                '5'
            ], capture_output=True, text=True, timeout=3600)

            if result.returncode == 0:
                print('✅ Pipeline complete for: ' + filename)
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
    run_watcher()