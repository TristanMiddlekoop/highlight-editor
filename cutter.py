import subprocess
import os

def cut_highlights(video_path, timestamps, clip_duration=14, format='vertical', output_dir=None):
    if output_dir is None:
        output_dir = os.path.expanduser('~/highlight-editor/output')
    
    os.makedirs(output_dir, exist_ok=True)

    if format == 'vertical':
        vf_filter = 'crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920'
        suffix = '_vertical'
    else:
        vf_filter = 'scale=1920:1080'
        suffix = '_horizontal'

    print('Cutting ' + str(len(timestamps)) + ' highlights in ' + format + ' format...')

    for i, timestamp in enumerate(timestamps):
        start = max(0, timestamp - 2)
        minutes = int(timestamp // 60)
        seconds = int(timestamp % 60)
        output_file = os.path.join(output_dir, 'highlight_' + str(i+1) + '_' + str(minutes) + 'm' + str(seconds) + 's' + suffix + '.mp4')

        command = [
            'ffmpeg',
            '-ss', str(start),
            '-i', video_path,
            '-t', str(clip_duration),
            '-vf', vf_filter,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-y',
            output_file
        ]

        print('Cutting highlight ' + str(i+1) + ' at ' + str(minutes) + ':' + str(seconds).zfill(2) + '...')
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print('  Saved: ' + os.path.basename(output_file))

    print('Done. ' + str(len(timestamps)) + ' clips saved to output folder')

if __name__ == '__main__':
    from detector import find_highlights
    video = os.path.expanduser('~/highlight-editor/test_videos/nba_test.webm')
    timestamps_raw = find_highlights(video, sensitivity=1.25)
    timestamps = [h['timestamp'] for h in timestamps_raw]
    cut_highlights(video, timestamps, format='vertical')