import os
import shutil
import json
from datetime import datetime
from scheduler import load_schedule


def create_export_package(output_dir=None):
    if output_dir is None:
        output_dir = os.path.expanduser('~/highlight-editor/output')

    export_dir = os.path.expanduser('~/highlight-editor/export')
    os.makedirs(export_dir, exist_ok=True)

    schedule = load_schedule()
    queue = [item for item in schedule.get('queue', []) if item['status'] == 'queued']

    if not queue:
        print('No queued posts found. Process a video and add clips to the schedule first.')
        return

    print('========================================')
    print('   EXPORT PACKAGE')
    print('========================================')
    print('Creating export package for ' + str(len(queue)) + ' queued posts...\n')

    for i, item in enumerate(queue):
        clip_path = item['clip_path']
        platform = item['platform']
        caption = item['caption']
        hashtags = item['hashtags']
        scheduled_time = item['scheduled_time']

        if not os.path.exists(clip_path):
            print('Clip not found: ' + clip_path)
            continue

        clip_name = os.path.basename(clip_path).replace('.mp4', '')
        post_dir = os.path.join(export_dir, 'post_' + str(i+1) + '_' + platform)
        os.makedirs(post_dir, exist_ok=True)

        dest_video = os.path.join(post_dir, os.path.basename(clip_path))
        shutil.copy2(clip_path, dest_video)

        caption_file = os.path.join(post_dir, 'caption.txt')
        with open(caption_file, 'w') as f:
            f.write('PLATFORM: ' + platform.upper() + '\n')
            f.write('SCHEDULED: ' + scheduled_time + '\n\n')
            f.write('CAPTION:\n')
            f.write(caption + '\n\n')
            f.write('HASHTAGS:\n')
            f.write(hashtags + '\n')

        print('Post ' + str(i+1) + ' — ' + platform.upper())
        print('  Scheduled: ' + scheduled_time)
        print('  Video: ' + os.path.basename(clip_path))
        print('  Caption: ' + caption[:50] + '...')
        print('  Saved to: ' + post_dir)
        print('')

    summary_file = os.path.join(export_dir, 'posting_schedule.txt')
    with open(summary_file, 'w') as f:
        f.write('POSTING SCHEDULE\n')
        f.write('================\n\n')
        for i, item in enumerate(queue):
            f.write('Post ' + str(i+1) + ' — ' + item['scheduled_time'] + '\n')
            f.write('Platform: ' + item['platform'].upper() + '\n')
            f.write('Video: ' + os.path.basename(item['clip_path']) + '\n')
            f.write('Caption: ' + item['caption'][:80] + '...\n\n')

    print('Summary saved to: ' + summary_file)
    print('\nExport complete. Open ~/highlight-editor/export/ to find your posts.')
    print('Each folder contains the video and caption ready to copy and post.')


if __name__ == '__main__':
    create_export_package()