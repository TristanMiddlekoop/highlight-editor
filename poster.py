import tweepy
import os
import json
from scheduler import load_schedule, save_schedule, get_due_posts, mark_as_posted


def get_x_client():
    api_key = os.environ.get('X_API_KEY')
    api_secret = os.environ.get('X_API_SECRET')
    access_token = os.environ.get('X_ACCESS_TOKEN')
    access_token_secret = os.environ.get('X_ACCESS_TOKEN_SECRET')

    if not all([api_key, api_secret, access_token, access_token_secret]):
        raise ValueError('X API keys not found. Check your environment variables.')

    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )

    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
    api = tweepy.API(auth)

    return client, api


def post_to_x(clip_path, caption, hashtags):
    print('Posting to X: ' + os.path.basename(clip_path))

    try:
        client, api = get_x_client()

        full_caption = caption + '\n\n' + hashtags

        if len(full_caption) > 280:
            full_caption = caption[:240] + '...\n\n' + hashtags[:30]

        if os.path.exists(clip_path):
            print('Uploading video...')
            media = api.media_upload(filename=clip_path, media_category='tweet_video', chunked=True)
            media_id = media.media_id

            print('Waiting for video processing...')
            import time
            for i in range(30):
                media_status = api.get_media_upload_status(media_id)
                state = media_status.processing_info.get('state', 'succeeded')
                if state == 'succeeded':
                    break
                elif state == 'failed':
                    raise Exception('Video processing failed')
                time.sleep(5)

            response = client.create_tweet(text=full_caption, media_ids=[media_id])
        else:
            response = client.create_tweet(text=full_caption)

        print('Posted successfully! Tweet ID: ' + str(response.data['id']))
        return True

    except Exception as e:
        print('Failed to post to X: ' + str(e))
        return False


def run_poster():
    print('========================================')
    print('   AUTO POSTER — CHECKING QUEUE')
    print('========================================')

    due_posts = get_due_posts()

    if not due_posts:
        print('No posts due right now.')
        return

    print('Found ' + str(len(due_posts)) + ' posts due:')

    for item in due_posts:
        print('\nPosting: ' + os.path.basename(item['clip_path']))
        print('Platform: ' + item['platform'])
        print('Scheduled: ' + item['scheduled_time'])

        if item['platform'] in ('twitter', 'x'):
            success = post_to_x(
                clip_path=item['clip_path'],
                caption=item['caption'],
                hashtags=item['hashtags']
            )
        else:
            print('Platform ' + item['platform'] + ' not yet supported — skipping')
            success = False

        if success:
            mark_as_posted(item['clip_path'])
            print('✅ Marked as posted')
        else:
            print('❌ Post failed')

    print('\nDone.')


if __name__ == '__main__':
    run_poster()