import json
import os
from datetime import datetime, timedelta


SCHEDULE_FILE = os.path.expanduser('~/highlight-editor/schedule.json')


def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, 'r') as f:
            return json.load(f)
    return {'posting_times': [], 'queue': []}


def save_schedule(schedule):
    with open(SCHEDULE_FILE, 'w') as f:
        json.dump(schedule, f, indent=2)
    print('Schedule saved to: ' + SCHEDULE_FILE)


def set_posting_times(times):
    schedule = load_schedule()
    schedule['posting_times'] = times
    save_schedule(schedule)
    print('Posting times set: ' + ', '.join(times))


def add_to_queue(clip_path, platform, caption, hashtags, scheduled_time=None):
    schedule = load_schedule()

    if scheduled_time is None:
        scheduled_time = get_next_slot(schedule)

    item = {
        'clip_path': clip_path,
        'platform': platform,
        'caption': caption,
        'hashtags': hashtags,
        'scheduled_time': scheduled_time,
        'status': 'queued',
        'added_at': datetime.now().isoformat()
    }

    schedule['queue'].append(item)
    save_schedule(schedule)
    print('Added to queue: ' + os.path.basename(clip_path) + ' → ' + scheduled_time)
    return item


def get_next_slot(schedule):
    posting_times = schedule.get('posting_times', [])
    if not posting_times:
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.strftime('%Y-%m-%d 09:00')

    queue = schedule.get('queue', [])
    used_slots = [item['scheduled_time'] for item in queue if item['status'] == 'queued']

    now = datetime.now()
    for days_ahead in range(7):
        check_date = now + timedelta(days=days_ahead)
        for time_str in sorted(posting_times):
            slot = check_date.strftime('%Y-%m-%d') + ' ' + time_str
            slot_dt = datetime.strptime(slot, '%Y-%m-%d %H:%M')
            if slot_dt > now and slot not in used_slots:
                return slot

    fallback = now + timedelta(hours=24)
    return fallback.strftime('%Y-%m-%d %H:%M')


def view_queue():
    schedule = load_schedule()
    queue = schedule.get('queue', [])
    times = schedule.get('posting_times', [])

    print('========================================')
    print('   POSTING SCHEDULE')
    print('========================================')
    print('Posting times: ' + (', '.join(times) if times else 'Not set'))
    print('')

    if not queue:
        print('Queue is empty')
        return

    queued = [i for i in queue if i['status'] == 'queued']
    posted = [i for i in queue if i['status'] == 'posted']

    print('QUEUED (' + str(len(queued)) + '):')
    for item in sorted(queued, key=lambda x: x['scheduled_time']):
        print('  → ' + item['scheduled_time'] + ' | ' + item['platform'].upper() + ' | ' + os.path.basename(item['clip_path']))
        print('    ' + item['caption'][:60] + '...')
        print('')

    if posted:
        print('POSTED (' + str(len(posted)) + '):')
        for item in posted:
            print('  ✅ ' + item['scheduled_time'] + ' | ' + os.path.basename(item['clip_path']))


def clear_queue():
    schedule = load_schedule()
    schedule['queue'] = []
    save_schedule(schedule)
    print('Queue cleared')


def get_due_posts():
    schedule = load_schedule()
    queue = schedule.get('queue', [])
    now = datetime.now()
    due = []
    for item in queue:
        if item['status'] == 'queued':
            scheduled = datetime.strptime(item['scheduled_time'], '%Y-%m-%d %H:%M')
            if scheduled <= now:
                due.append(item)
    return due


def mark_as_posted(clip_path):
    schedule = load_schedule()
    for item in schedule['queue']:
        if item['clip_path'] == clip_path and item['status'] == 'queued':
            item['status'] = 'posted'
            item['posted_at'] = datetime.now().isoformat()
    save_schedule(schedule)


if __name__ == '__main__':
    print('Setting up test schedule...')
    set_posting_times(['09:00', '12:00', '18:00'])

    add_to_queue(
        clip_path='~/highlight-editor/output/highlight_1_0m0s_vertical.mp4',
        platform='instagram',
        caption='OH MY! This play had the crowd going crazy 🔥',
        hashtags='#basketball #hoops #highlights'
    )

    add_to_queue(
        clip_path='~/highlight-editor/output/highlight_2_4m3s_vertical.mp4',
        platform='tiktok',
        caption='When the offense clicks like this 👌',
        hashtags='#basketball #sportsclips #viral'
    )

    view_queue()