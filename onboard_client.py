import os
import json
import sys
sys.path.insert(0, os.path.expanduser('~/highlight-editor'))
from client_manager import create_client, add_player, update_branding, save_client, load_client

def onboard_client():
    print('========================================')
    print('   HIGHLIGHTOS — CLIENT ONBOARDING')
    print('========================================')
    print('Welcome to the HighlightOS onboarding flow.')
    print('This will set up a new client in under 10 minutes.')
    print('')

    # Basic info
    print('STEP 1 — ORGANIZATION INFO')
    print('─' * 30)
    client_name = input('Organization name (e.g. Naples Eagles): ').strip()
    team_name = input('Team name (e.g. Naples Eagles Basketball): ').strip()
    client_id = input('Client ID — no spaces (e.g. naples_eagles_basketball): ').strip().lower().replace(' ', '_')
    league = input('League (e.g. Florida High School Basketball): ').strip()
    contact_email = input('Contact email: ').strip()

    # Sport
    print('')
    print('STEP 2 — SPORT')
    print('─' * 30)
    print('Available sports: basketball, football, soccer, baseball, volleyball, hockey, tennis, mma, darts')
    sport = input('Sport: ').strip().lower()

    # Branding
    print('')
    print('STEP 3 — BRANDING')
    print('─' * 30)
    print('Enter primary team color as RGB values (e.g. 255 140 0 for orange)')
    color_input = input('Primary color RGB (press enter to skip): ').strip()
    if color_input:
        try:
            r, g, b = map(int, color_input.split())
            team_color = [r, g, b]
        except:
            print('Invalid color format — using default orange')
            team_color = [255, 140, 0]
    else:
        team_color = [255, 140, 0]

    # Social platforms
    print('')
    print('STEP 4 — SOCIAL PLATFORMS')
    print('─' * 30)
    print('Available: instagram, tiktok, youtube, twitter')
    platforms_input = input('Platforms (comma separated, e.g. instagram,tiktok): ').strip()
    platforms = [p.strip().lower() for p in platforms_input.split(',')] if platforms_input else ['instagram']

    # Create client
    print('')
    print('Creating client...')
    config = create_client(
        client_id=client_id,
        client_name=client_name,
        sport=sport,
        team_name=team_name,
        league=league
    )

    if not config:
        print('❌ Failed to create client')
        return

    # Update with additional info
    config['contact_email'] = contact_email
    config['branding']['primary_color'] = team_color
    config['branding']['watermark_text'] = team_name
    config['posting']['platforms'] = platforms
    save_client(client_id, config)

    # Players
    print('')
    print('STEP 5 — PLAYER ROSTER')
    print('─' * 30)
    print('Add players to the roster. Press enter with no name to finish.')
    print('')

    player_count = 0
    while True:
        name = input('Player name (or press enter to finish): ').strip()
        if not name:
            break
        number = input('Jersey number: ').strip()
        position = input('Position: ').strip()
        fun_fact = input('Fun fact (optional): ').strip()
        add_player(client_id, name, int(number) if number.isdigit() else 0, position, fun_fact=fun_fact)
        player_count += 1
        print('✅ Added ' + name)
        print('')

    # Sync to portal
    print('')
    print('Syncing to client portal...')
    portal_clients_file = os.path.expanduser('~/highlight-editor/portal/clients.json')
    final_config = load_client(client_id)
    if final_config:
        # Load existing portal clients
        if os.path.exists(portal_clients_file):
            with open(portal_clients_file, 'r') as f:
                try:
                    portal_data = json.load(f)
                    if 'client_id' in portal_data:
                        portal_data = {portal_data['client_id']: portal_data}
                except:
                    portal_data = {}
        else:
            portal_data = {}

        portal_data[client_id] = final_config
        with open(portal_clients_file, 'w') as f:
            json.dump(portal_data, f, indent=2)
        print('✅ Portal synced')

    # Summary
    print('')
    print('========================================')
    print('   ONBOARDING COMPLETE')
    print('========================================')
    print('Client:    ' + client_name)
    print('Sport:     ' + sport.capitalize())
    print('League:    ' + league)
    print('Email:     ' + contact_email)
    print('Players:   ' + str(player_count))
    print('Platforms: ' + ', '.join(platforms))
    print('')
    print('Inbox folder: ~/highlight-editor/clients/' + client_id + '/inbox/')
    print('Portal:       https://portal.tmventures.io')
    print('')
    print('Next steps:')
    print('1. Send client their portal login link')
    print('2. They drop footage into their inbox folder')
    print('3. Run: python3 watcher.py clients')
    print('4. Pipeline processes automatically')
    print('========================================')


if __name__ == '__main__':
    onboard_client()