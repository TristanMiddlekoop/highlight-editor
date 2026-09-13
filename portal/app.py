from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json

app = Flask(__name__)
app.secret_key = 'highlightos-tm-ventures-2026'

DEMO_CLIENTS = {
    'naples_eagles_basketball': {
        'client_id': 'naples_eagles_basketball',
        'client_name': 'Naples Eagles',
        'team_name': 'Naples Eagles Basketball',
        'sport': 'basketball',
        'league': 'Florida High School Basketball',
        'contact_email': 'coach@napleseagles.com',
        'players': [
            {'number': 23, 'name': 'Marcus Johnson', 'position': 'Point Guard'},
            {'number': 11, 'name': 'Tyler Williams', 'position': 'Small Forward'},
            {'number': 5, 'name': 'Jordan Davis', 'position': 'Center'},
        ]
    }
}


def get_client_by_email(email):
    for client_id, client in DEMO_CLIENTS.items():
        if client.get('contact_email', '').lower() == email.lower():
            return client
    return None


def load_client(client_id):
    return DEMO_CLIENTS.get(client_id)


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
