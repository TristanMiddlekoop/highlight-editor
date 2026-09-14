from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json

app = Flask(__name__)
app.secret_key = 'highlightos-tm-ventures-2026'

CLIENTS_FILE = os.path.join(os.path.dirname(__file__), 'clients.json')


def load_all_clients():
    if os.path.exists(CLIENTS_FILE):
        with open(CLIENTS_FILE, 'r') as f:
            data = json.load(f)
            if 'client_id' in data:
                return {data['client_id']: data}
            return data
    return {}


def get_client_by_email(email):
    clients = load_all_clients()
    for client_id, client in clients.items():
        if client.get('contact_email', '').lower() == email.lower():
            return client
    return None


def load_client(client_id):
    clients = load_all_clients()
    return clients.get(client_id)


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
    return render_template('dashboard.html',
        client=config,
        clips=[],
        inbox_count=0,
        clip_count=0
    )


@app.route('/upload', methods=['POST'])
def upload():
    if 'client_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    return jsonify({'success': True, 'message': 'Video received. Processing will begin shortly.'})


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/health')
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(debug=True, port=5001)
