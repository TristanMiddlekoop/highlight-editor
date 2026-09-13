from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json
import sys
sys.path.insert(0, os.path.expanduser('~/highlight-editor'))
from client_manager import load_client, list_clients, get_client_inbox, get_client_output
from analytics import load_analytics

app = Flask(__name__)
app.secret_key = 'highlightos-tm-ventures-2026'

CLIENTS_DIR = os.path.expanduser('~/highlight-editor/clients')


def get_client_by_email(email):
    clients = list_clients()
    for client in clients:
        if client.get('contact_email', '').lower() == email.lower():
            return client
    return None


@app.route('/')
def index():
    if 'client_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email', '').strip()
    client = get_client_by_email(email)
    if client:
        session['client_id'] = client['client_id']
        session['client_name'] = client['client_name']
        return redirect(url_for('dashboard'))
    return render_template('login.html', error='No account found with that email.')


@app.route('/dashboard')
def dashboard():
    if 'client_id' not in session:
        return redirect(url_for('index'))
    client_id = session['client_id']
    config = load_client(client_id)
    if not config:
        return redirect(url_for('logout'))
    output = get_client_output(client_id)
    import glob
    clips = sorted(glob.glob(os.path.join(output, '*_vertical_overlay.mp4')))
    inbox = get_client_inbox(client_id)
    inbox_files = glob.glob(os.path.join(inbox, '*.mp4')) + glob.glob(os.path.join(inbox, '*.mov'))
    return render_template('dashboard.html',
        client=config,
        clips=clips,
        inbox_count=len(inbox_files),
        clip_count=len(clips)
    )


@app.route('/upload', methods=['POST'])
def upload():
    if 'client_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    client_id = session['client_id']
    inbox = get_client_inbox(client_id)
    os.makedirs(inbox, exist_ok=True)
    if 'video' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    filename = file.filename
    filepath = os.path.join(inbox, filename)
    file.save(filepath)
    return jsonify({'success': True, 'message': 'Video uploaded successfully. Processing will begin shortly.'})


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/api/status')
def api_status():
    if 'client_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    client_id = session['client_id']
    config = load_client(client_id)
    output = get_client_output(client_id)
    inbox = get_client_inbox(client_id)
    import glob
    clips = glob.glob(os.path.join(output, '*_vertical_overlay.mp4'))
    inbox_files = glob.glob(os.path.join(inbox, '*.mp4'))
    return jsonify({
        'client_name': config['client_name'],
        'clips_ready': len(clips),
        'processing': len(inbox_files),
        'sport': config['sport'],
        'players': len(config.get('players', []))
    })


if __name__ == '__main__':
    app.run(debug=True, port=5001)