import os
import sys
from detector import find_highlights, SPORT_PRESETS
from cutter import cut_highlights
from exporter import stitch_highlights
from captions import caption_all_clips

def run(video_path, mode='both', sport='general', top_n=None, captions=False, font_size=1.0, position=0.82):
    video_path = os.path.expanduser(video_path)
    if not os.path.exists(video_path):
        print('Error: Video file not found at ' + video_path)
        return

    preset = SPORT_PRESETS.get(sport, SPORT_PRESETS['general'])
    sensitivity = preset['sensitivity']
    min_gap = preset['min_gap']
    clip_duration = preset['clip_duration']

    print('========================================')
    print('   AI SPORTS HIGHLIGHT EDITOR')
    print('========================================')
    print('Video: ' + os.path.basename(video_path))
    print('Sport: ' + sport.upper())
    print('Mode: ' + mode)
    print('Captions: ' + str(captions))
    if captions:
        print('Font size: ' + str(font_size) + ' | Position: ' + str(position))
    if top_n:
        print('Top clips: ' + str(top_n))
    print('========================================')

    highlights = find_highlights(video_path, sensitivity=sensitivity, min_gap=min_gap)

    # Sort by hype score, take top N
    highlights = sorted(highlights, key=lambda x: x['score'], reverse=True)
    if top_n and len(highlights) > top_n:
        highlights = highlights[:top_n]
        print('Trimmed to top ' + str(top_n) + ' highlights by hype score')

    # Sort back into chronological order for cutting
    highlights = sorted(highlights, key=lambda x: x['timestamp'])

    print('Found ' + str(len(highlights)) + ' highlights:')
    for h in highlights:
        minutes = int(h['timestamp'] // 60)
        seconds = int(h['timestamp'] % 60)
        flame = ' 🔥' if h['score'] >= 70 else ''
        print('  → ' + str(minutes) + ':' + str(seconds).zfill(2) + ' — Score: ' + str(h['score']) + flame)
    print('')

    timestamps = [h['timestamp'] for h in highlights]
    new_vertical_clips = []

    if mode in ('short', 'both'):
        print('--- SHORT FORM --- vertical 9:16 ---')
        cut_highlights(video_path, timestamps, clip_duration=clip_duration, format='vertical')
        for i, t in enumerate(timestamps):
            minutes = int(t // 60)
            seconds = int(t % 60)
            fname = 'highlight_' + str(i+1) + '_' + str(minutes) + 'm' + str(seconds) + 's_vertical.mp4'
            new_vertical_clips.append(fname)
        if captions:
            caption_all_clips('~/highlight-editor/output', format='vertical', new_clips_only=new_vertical_clips, font_size=font_size, position=position)
        print('')

    if mode in ('long', 'both'):
        print('--- LONG FORM --- horizontal 16:9 ---')
        cut_highlights(video_path, timestamps, clip_duration=clip_duration, format='horizontal')
        stitch_highlights('~/highlight-editor/output', final_output_name='highlight_reel_horizontal.mp4')
        print('')

    print('DONE. Check ~/highlight-editor/output/')
    print('  Short form: individual _vertical.mp4 clips')
    if captions:
        print('  Captioned:  individual _vertical_captioned.mp4 clips')
    print('  Long form:  highlight_reel_horizontal.mp4')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python3 main.py <video> [short/long/both] [sport] [top_n] [captions] [font_size] [position]')
        print('Example: python3 main.py video.mp4 both basketball 5 captions 1.3 0.88')
    else:
        video = sys.argv[1]
        mode = sys.argv[2] if len(sys.argv) > 2 else 'both'
        sport = sys.argv[3] if len(sys.argv) > 3 else 'general'
        top_n = int(sys.argv[4]) if len(sys.argv) > 4 else None
        captions = sys.argv[5] == 'captions' if len(sys.argv) > 5 else False
        font_size = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0
        position = float(sys.argv[7]) if len(sys.argv) > 7 else 0.82
        run(video, mode=mode, sport=sport, top_n=top_n, captions=captions, font_size=font_size, position=position)