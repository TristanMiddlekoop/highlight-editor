import os
import requests
import webbrowser
import json
import hashlib
import base64
import secrets
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, urlparse, parse_qs


CLIENT_KEY = os.environ.get('TIKTOK_CLIENT_KEY')
CLIENT_SECRET = os.environ.get('TIKTOK_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8080'
TOKEN_FILE = os.path.expanduser('~/highlight-editor/tiktok_token.json')
VERIFIER_FILE = os.path.expanduser('~/highlight-editor/tiktok_verifier.txt')


class AuthHandler(BaseHTTPRequestHandler):
    auth_code = None

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if 'code' in params:
            AuthHandler.auth_code = params['code'][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Authentication successful! You can close this window.')
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Authentication failed.')

    def log_message(self, format, *args):
        pass


def get_auth_code():
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode()

    with open(VERIFIER_FILE, 'w') as f:
        f.write(code_verifier)

    params = {
        'client_key': CLIENT_KEY,
        'scope': 'video.upload',
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'state': 'tm_ventures_highlight_editor',
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    auth_url = 'https://www.tiktok.com/v2/auth/authorize/?' + urlencode(params)
    print('Opening TikTok authorization...')
    webbrowser.open(auth_url)

    server = HTTPServer(('localhost', 8080), AuthHandler)
    server.handle_request()
    return AuthHandler.auth_code


def get_access_token(auth_code):
    code_verifier = ''
    if os.path.exists(VERIFIER_FILE):
        with open(VERIFIER_FILE, 'r') as f:
            code_verifier = f.read().strip()

    url = 'https://open.tiktokapis.com/v2/oauth/token/'
    data = {
        'client_key': CLIENT_KEY,
        'client_secret': CLIENT_SECRET,
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
        'code_verifier': code_verifier
    }
    response = requests.post(url, data=data)
    token_data = response.json()

    if 'access_token' in token_data:
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f)
        print('Access token saved successfully')
        return token_data['access_token'], token_data.get('open_id')
    else:
        print('Failed to get access token: ' + str(token_data))
        return None, None


def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            data = json.load(f)
            return data.get('access_token'), data.get('open_id')
    return None, None


def upload_to_tiktok(clip_path, caption, hashtags):
    print('Uploading to TikTok: ' + os.path.basename(clip_path))

    access_token, open_id = load_token()

    if not access_token:
        print('No token found. Authenticating...')
        auth_code = get_auth_code()
        if not auth_code:
            print('Authentication failed')
            return False
        access_token, open_id = get_access_token(auth_code)

    if not access_token:
        print('Could not get access token')
        return False

    try:
        video_size = os.path.getsize(clip_path)

        init_url = 'https://open.tiktokapis.com/v2/post/publish/inbox/video/init/'
        headers = {
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'application/json'
        }
        init_data = {
            'source_info': {
                'source': 'FILE_UPLOAD',
                'video_size': video_size,
                'chunk_size': video_size,
                'total_chunk_count': 1
            }
        }

        init_response = requests.post(init_url, headers=headers, json=init_data)
        init_result = init_response.json()

        if init_result.get('error', {}).get('code') != 'ok':
            print('Init failed: ' + str(init_result))
            return False

        upload_url = init_result['data']['upload_url']
        publish_id = init_result['data']['publish_id']

        print('Uploading video file...')
        with open(clip_path, 'rb') as f:
            video_data = f.read()

        upload_headers = {
            'Content-Range': 'bytes 0-' + str(video_size - 1) + '/' + str(video_size),
            'Content-Type': 'video/mp4'
        }
        upload_response = requests.put(upload_url, headers=upload_headers, data=video_data)

        if upload_response.status_code in (200, 201, 204):
            print('✅ Video uploaded to TikTok inbox! Publish ID: ' + publish_id)
            print('Open TikTok to find the video in your inbox and complete posting.')
            return True
        else:
            print('Upload failed: ' + str(upload_response.status_code))
            return False

    except Exception as e:
        print('Upload failed: ' + str(e))
        return False


if __name__ == '__main__':
    test_clip = os.path.expanduser('~/highlight-editor/output/highlight_1_0m8s_vertical.mp4')

    if os.path.exists(test_clip):
        upload_to_tiktok(
            clip_path=test_clip,
            caption='Sports highlight — AI generated 🔥',
            hashtags='#sports #highlights #basketball #AI #TMVentures'
        )
    else:
        print('Test clip not found. Process a video first.')