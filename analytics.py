import os
import json
import glob
from datetime import datetime, timedelta
from collections import defaultdict


ANALYTICS_FILE = os.path.expanduser('~/highlight-editor/analytics.json')
OUTPUT_DIR = os.path.expanduser('~/highlight-editor/output')
PROCESSED_DIR = os.path.expanduser('~/highlight-editor/watch_processed')
SCHEDULE_FILE = os.path.expanduser('~/highlight-editor/schedule.json')


def load_analytics():
    if os.path.exists(ANALYTICS_FILE):
        with open(ANALYTICS_FILE, 'r') as f:
            return json.load(f)
    return {
        'videos_processed': [],
        'clips_generated': [],
        'posts_scheduled': [],
        'posts_published': [],
        'platform_stats': {},
        'sport_stats': {}
    }


def save_analytics(data):
    with open(ANALYTICS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def track_video_processed(filename, sport, clips_count, duration_seconds=None):
    analytics = load_analytics()
    entry = {
        'filename': filename,
        'sport': sport,
        'clips_generated': clips_count,
        'processed_at': datetime.now().isoformat(),
        'duration_seconds': duration_seconds
    }
    analytics['videos_processed'].append(entry)

    if sport not in analytics['sport_stats']:
        analytics['sport_stats'][sport] = {'videos': 0, 'clips': 0}
    analytics['sport_stats'][sport]['videos'] += 1
    analytics['sport_stats'][sport]['clips'] += clips_count

    save_analytics(analytics)
    print('📊 Tracked: ' + filename + ' (' + sport + ', ' + str(clips_count) + ' clips)')


def track_post_published(platform, clip_name, video_id=None):
    analytics = load_analytics()
    entry = {
        'platform': platform,
        'clip_name': clip_name,
        'video_id': video_id,
        'published_at': datetime.now().isoformat()
    }
    analytics['posts_published'].append(entry)

    if platform not in analytics['platform_stats']:
        analytics['platform_stats'][platform] = {'posts': 0}
    analytics['platform_stats'][platform]['posts'] += 1

    save_analytics(analytics)


def get_dashboard():
    analytics = load_analytics()

    schedule_data = {'queue': []}
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, 'r') as f:
            schedule_data = json.load(f)

    processed_files = glob.glob(os.path.join(PROCESSED_DIR, '*'))
    output_files = glob.glob(os.path.join(OUTPUT_DIR, '*.mp4'))
    vertical_clips = [f for f in output_files if '_vertical' in f and '_captioned' not in f]
    horizontal_clips = [f for f in output_files if '_horizontal' in f and 'reel' not in f]

    total_videos = len(analytics['videos_processed']) + len(processed_files)
    total_clips = len(vertical_clips) + len(horizontal_clips)
    total_published = len(analytics['posts_published'])
    queued_posts = len([p for p in schedule_data['queue'] if p['status'] == 'queued'])
    posted = len([p for p in schedule_data['queue'] if p['status'] == 'posted'])

    now = datetime.now()
    week_ago = now - timedelta(days=7)
    recent_processed = [
        v for v in analytics['videos_processed']
        if datetime.fromisoformat(v['processed_at']) > week_ago
    ]

    sport_breakdown = analytics.get('sport_stats', {})
    platform_breakdown = analytics.get('platform_stats', {})

    print('========================================')
    print('   TM VENTURES — ANALYTICS DASHBOARD')
    print('========================================')
    print('')
    print('📊 OVERALL STATS')
    print('  Videos processed:     ' + str(total_videos))
    print('  Clips in output:      ' + str(total_clips))
    print('  Posts queued:         ' + str(queued_posts))
    print('  Posts published:      ' + str(total_published + posted))
    print('')
    print('📅 THIS WEEK')
    print('  Videos processed:     ' + str(len(recent_processed)))
    print('')

    if sport_breakdown:
        print('🏆 BY SPORT')
        for sport, stats in sport_breakdown.items():
            print('  ' + sport.capitalize() + ': ' + str(stats['videos']) + ' videos, ' + str(stats['clips']) + ' clips')
        print('')

    if platform_breakdown:
        print('📱 BY PLATFORM')
        for platform, stats in platform_breakdown.items():
            print('  ' + platform.capitalize() + ': ' + str(stats['posts']) + ' posts')
        print('')

    queue = schedule_data.get('queue', [])
    upcoming = [p for p in queue if p['status'] == 'queued']
    if upcoming:
        print('🕐 UPCOMING POSTS')
        for post in sorted(upcoming, key=lambda x: x['scheduled_time'])[:5]:
            print('  ' + post['scheduled_time'] + ' | ' + post['platform'].upper() + ' | ' + os.path.basename(post['clip_path']))
        print('')

    recent_published = sorted(
        analytics['posts_published'],
        key=lambda x: x['published_at'],
        reverse=True
    )[:5]
    if recent_published:
        print('✅ RECENTLY PUBLISHED')
        for post in recent_published:
            print('  ' + post['published_at'][:16] + ' | ' + post['platform'].upper() + ' | ' + post['clip_name'])
        print('')

    print('========================================')

    return {
        'total_videos': total_videos,
        'total_clips': total_clips,
        'queued_posts': queued_posts,
        'total_published': total_published + posted,
        'sport_breakdown': sport_breakdown,
        'platform_breakdown': platform_breakdown
    }


if __name__ == '__main__':
    get_dashboard()