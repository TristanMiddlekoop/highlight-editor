import subprocess
import os
import glob
import re

def get_timestamp_seconds(filename):
    match = re.search(r'highlight_\d+_(\d+)m(\d+)s', filename)
    if match:
        minutes = int(match.group(1))
        seconds = int(match.group(2))
        return minutes * 60 + seconds
    return 0

def stitch_highlights(output_dir, final_output_name='highlight_reel_horizontal.mp4', format='horizontal'):
    if isinstance(output_dir, str) and output_dir.startswith('~'):
        output_dir = os.path.expanduser(output_dir)

    clips = glob.glob(os.path.join(output_dir, 'highlight_*_' + format + '.mp4'))
    clips = sorted(clips, key=get_timestamp_seconds)

    if not clips:
        print('No ' + format + ' clips found in output folder')
        return

    print('Found ' + str(len(clips)) + ' clips to stitch in chronological order...')

    list_file = os.path.join(output_dir, 'clips_list.txt')
    with open(list_file, 'w') as f:
        for clip in clips:
            f.write('file ' + clip + '\n')

    final_output = os.path.join(output_dir, final_output_name)

    command = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', list_file,
        '-c', 'copy',
        '-y',
        final_output
    ]

    print('Stitching clips together...')
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print('Done. Highlight reel saved as: ' + final_output_name)

    if os.path.exists(list_file):
        os.remove(list_file)

if __name__ == '__main__':
    stitch_highlights('~/highlight-editor/output')