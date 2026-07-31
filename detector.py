import librosa
import numpy as np
import subprocess
import os
import tempfile

SPORT_PRESETS = {
    'basketball': {'sensitivity': 1.25, 'min_gap': 30, 'clip_duration': 14},
    'soccer':     {'sensitivity': 1.4,  'min_gap': 45, 'clip_duration': 20},
    'mma':        {'sensitivity': 1.1,  'min_gap': 20, 'clip_duration': 16},
    'football':   {'sensitivity': 1.3,  'min_gap': 35, 'clip_duration': 14},
    'hockey':     {'sensitivity': 1.2,  'min_gap': 25, 'clip_duration': 14},
    'cricket':    {'sensitivity': 1.5,  'min_gap': 40, 'clip_duration': 18},
    'tennis':     {'sensitivity': 1.3,  'min_gap': 20, 'clip_duration': 12},
    'darts':      {'sensitivity': 1.2,  'min_gap': 15, 'clip_duration': 10},
    'general':    {'sensitivity': 1.25, 'min_gap': 30, 'clip_duration': 14},
}

def extract_audio_to_wav(video_path):
    tmp_wav = tempfile.mktemp(suffix='.wav')
    command = [
        'ffmpeg', '-i', video_path,
        '-ac', '1', '-ar', '22050',
        '-y', tmp_wav
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return tmp_wav

def find_highlights(video_path, sensitivity=1.25, min_gap=30):
    print('Loading video: ' + video_path)
    tmp_wav = extract_audio_to_wav(video_path)
    audio, sample_rate = librosa.load(tmp_wav, mono=True)
    os.remove(tmp_wav)
    print('Audio extracted successfully')

    energy = librosa.feature.rms(y=audio)[0]
    avg_energy = np.mean(energy)
    max_energy = np.max(energy)
    threshold = avg_energy * (1 + sensitivity)
    frame_duration = librosa.get_duration(y=audio, sr=sample_rate) / len(energy)

    highlights = []
    for i, e in enumerate(energy):
        if e > threshold:
            timestamp = i * frame_duration
            if not highlights or timestamp - highlights[-1]['timestamp'] > min_gap:
                score = int(((e - threshold) / (max_energy - threshold)) * 100)
                highlights.append({
                    'timestamp': timestamp,
                    'score': score
                })

    return highlights

if __name__ == '__main__':
    video = os.path.expanduser('~/highlight-editor/test_videos/nba_test.webm')
    highlights = find_highlights(video)
    print('Found ' + str(len(highlights)) + ' highlight moments:')
    sorted_highlights = sorted(highlights, key=lambda x: x['score'], reverse=True)
    for h in sorted_highlights:
        minutes = int(h['timestamp'] // 60)
        seconds = int(h['timestamp'] % 60)
        flame = ' 🔥' if h['score'] >= 70 else ''
        print('  → ' + str(minutes) + ':' + str(seconds).zfill(2) + ' — Score: ' + str(h['score']) + flame)