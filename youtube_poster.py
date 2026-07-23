import os
import pickle
import google.oauth2.credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CREDENTIALS_FILE = os.path.expanduser('~/highlight-editor/youtube_credentials.json')
TOKEN_FILE = os.path.expanduser('~/highlight-editor/youtube_token.pickle')


def get_youtube_client():
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)

        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    youtube = build('youtube', 'v3', credentials=creds)
    return youtube


def upload_to_youtube(clip_path, title, description, tags=None, privacy='private'):
    print('Uploading to YouTube: ' + os.path.basename(clip_path))

    try:
        youtube = get_youtube_client()

        if tags is None:
            tags = ['sports', 'highlights', 'AI']

        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '17'
            },
            'status': {
                'privacyStatus': privacy
            }
        }

        media = MediaFileUpload(
            clip_path,
            mimetype='video/mp4',
            resumable=True
        )

        request = youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print('Upload progress: ' + str(progress) + '%')

        print('✅ Uploaded successfully! Video ID: ' + response['id'])
        print('URL: https://www.youtube.com/watch?v=' + response['id'])
        return response['id']

    except Exception as e:
        print('❌ Upload failed: ' + str(e))
        return None


if __name__ == '__main__':
    test_clip = os.path.expanduser('~/highlight-editor/output/highlight_1_0m8s_vertical.mp4')

    if os.path.exists(test_clip):
        upload_to_youtube(
            clip_path=test_clip,
            title='Sports Highlight — AI Generated',
            description='Automatically generated highlight clip by TM Ventures AI Highlight Editor.',
            tags=['sports', 'highlights', 'basketball', 'AI', 'TMVentures'],
            privacy='private'
        )
    else:
        print('Test clip not found. Process a video first.')