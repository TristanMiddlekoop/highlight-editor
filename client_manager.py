import os
import json
from datetime import datetime

CLIENTS_DIR = os.path.expanduser('~/highlight-editor/clients')
os.makedirs(CLIENTS_DIR, exist_ok=True)


def create_client(client_id, client_name, sport, team_name, league=''):
    client_dir = os.path.join(CLIENTS_DIR, client_id)
    os.makedirs(client_dir, exist_ok=True)
    os.makedirs(os.path.join(client_dir, 'inbox'), exist_ok=True)
    os.makedirs(os.path.join(client_dir, 'output'), exist_ok=True)
    os.makedirs(os.path.join(client_dir, 'reports'), exist_ok=True)

    config = {
        'client_id': client_id,
        'client_name': client_name,
        'team_name': team_name,
        'sport': sport,
        'league': league,
        'created_at': datetime.now().isoformat(),
        'active': True,
        'branding': {
            'primary_color': [255, 140, 0],
            'secondary_color': [255, 255, 255],
            'logo_path': '',
            'watermark_text': team_name
        },
        'overlay_settings': {
            'show_scoreboard': True,
            'show_lower_third': True,
            'show_label': True,
            'show_ticker': True
        },
        'posting': {
            'platforms': ['youtube'],
            'schedule_times': ['09:00', '12:00', '18:00'],
            'auto_post': False
        },
        'social_accounts': {
            'youtube_channel_id': '',
            'instagram_account': '',
            'tiktok_account': '',
            'twitter_account': ''
        },
        'players': []
    }

    config_path = os.path.join(client_dir, 'config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print('✅ Client created: ' + client_name + ' (' + client_id + ')')
    print('📁 Client folder: ' + client_dir)
    return config


def load_client(client_id):
    config_path = os.path.join(CLIENTS_DIR, client_id, 'config.json')
    if not os.path.exists(config_path):
        print('❌ Client not found: ' + client_id)
        return None
    with open(config_path, 'r') as f:
        return json.load(f)


def save_client(client_id, config):
    config_path = os.path.join(CLIENTS_DIR, client_id, 'config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


def add_player(client_id, name, number, position, photo_path='', fun_fact=''):
    config = load_client(client_id)
    if not config:
        return False

    player = {
        'id': 'player_' + str(len(config['players']) + 1),
        'name': name,
        'number': number,
        'position': position,
        'photo_path': photo_path,
        'fun_fact': fun_fact,
        'added_at': datetime.now().isoformat()
    }

    config['players'].append(player)
    save_client(client_id, config)
    print('✅ Player added: ' + name + ' #' + str(number) + ' (' + position + ')')
    return player


def list_clients():
    clients = []
    if not os.path.exists(CLIENTS_DIR):
        return clients
    for client_id in os.listdir(CLIENTS_DIR):
        config = load_client(client_id)
        if config:
            clients.append(config)
    return clients


def get_client_inbox(client_id):
    return os.path.join(CLIENTS_DIR, client_id, 'inbox')


def get_client_output(client_id):
    return os.path.join(CLIENTS_DIR, client_id, 'output')


def get_client_reports(client_id):
    return os.path.join(CLIENTS_DIR, client_id, 'reports')


def update_branding(client_id, primary_color=None, logo_path=None, watermark_text=None):
    config = load_client(client_id)
    if not config:
        return False
    if primary_color:
        config['branding']['primary_color'] = primary_color
    if logo_path:
        config['branding']['logo_path'] = logo_path
    if watermark_text:
        config['branding']['watermark_text'] = watermark_text
    save_client(client_id, config)
    print('✅ Branding updated for: ' + config['client_name'])
    return True


def print_client_summary(client_id):
    config = load_client(client_id)
    if not config:
        return
    print('========================================')
    print('   CLIENT: ' + config['client_name'].upper())
    print('========================================')
    print('ID:       ' + config['client_id'])
    print('Sport:    ' + config['sport'].capitalize())
    print('Team:     ' + config['team_name'])
    print('League:   ' + config['league'])
    print('Active:   ' + str(config['active']))
    print('Players:  ' + str(len(config['players'])))
    print('Platforms: ' + ', '.join(config['posting']['platforms']))
    print('')
    if config['players']:
        print('ROSTER:')
        for p in config['players']:
            print('  #' + str(p['number']) + ' ' + p['name'] + ' — ' + p['position'])
    print('========================================')


if __name__ == '__main__':
    # Test — create a demo client
    config = create_client(
        client_id='naples_eagles_basketball',
        client_name='Naples Eagles',
        sport='basketball',
        team_name='Naples Eagles',
        league='Florida High School Basketball'
    )

    add_player('naples_eagles_basketball', 'Marcus Johnson', 23, 'Point Guard',
               fun_fact='Averaging 18 points per game this season')
    add_player('naples_eagles_basketball', 'Tyler Williams', 11, 'Small Forward',
               fun_fact='Committed to University of Florida')
    add_player('naples_eagles_basketball', 'Jordan Davis', 5, 'Center',
               fun_fact='Team captain and defensive anchor')

    print_client_summary('naples_eagles_basketball')