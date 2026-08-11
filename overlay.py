import cv2
import os
import glob
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONTS_DIR = os.path.expanduser('~/highlight-editor/fonts')
FONT_BOLD = '/System/Library/Fonts/SFNSMono.ttf'
FONT_REGULAR = '/System/Library/Fonts/SFNSMono.ttf'
FONT_LIGHT = '/System/Library/Fonts/Geneva.ttf'


def get_font(style='bold', size=20):
    try:
        if style == 'bold':
            return ImageFont.truetype(FONT_BOLD, size)
        elif style == 'regular':
            return ImageFont.truetype(FONT_REGULAR, size)
        elif style == 'light':
            return ImageFont.truetype(FONT_LIGHT, size)
    except:
        return ImageFont.load_default()


def draw_text_pil(frame, text, x, y, font, color=(255, 255, 255), anchor='la'):
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    draw.text((x, y), text, font=font, fill=color[::-1], anchor=anchor)
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


def get_text_size_pil(text, font):
    img = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_scoreboard(frame, home_team, away_team,
                    home_score, away_score,
                    game_time='00:00', period='Q1', ticker_text='', sport='basketball'):
    h, w = frame.shape[:2]

    sb_h = int(h * 0.10)
    sb_w = int(w * 0.85)
    sb_x = (w - sb_w) // 2
    sb_y = int(h * 0.03)

    # Shadow
    shadow = frame.copy()
    cv2.rectangle(shadow, (sb_x - 4, sb_y - 4), (sb_x + sb_w + 4, sb_y + sb_h + 4), (0, 0, 0), -1)
    cv2.addWeighted(shadow, 0.45, frame, 0.55, 0, frame)

    # Main background
    overlay = frame.copy()
    cv2.rectangle(overlay, (sb_x, sb_y), (sb_x + sb_w, sb_y + sb_h), (18, 18, 22), -1)
    cv2.addWeighted(overlay, 0.90, frame, 0.10, 0, frame)

    # Orange top accent
    cv2.rectangle(frame, (sb_x, sb_y), (sb_x + sb_w, sb_y + 4), (255, 140, 0), -1)

    # Section widths
    team_w = int(sb_w * 0.28)
    score_w = int(sb_w * 0.13)
    center_w = sb_w - (team_w * 2) - (score_w * 2)

    # Team backgrounds
    team_bg = frame.copy()
    cv2.rectangle(team_bg, (sb_x, sb_y + 4), (sb_x + team_w, sb_y + sb_h), (28, 28, 38), -1)
    cv2.rectangle(team_bg, (sb_x + sb_w - team_w, sb_y + 4), (sb_x + sb_w, sb_y + sb_h), (28, 28, 38), -1)
    cv2.addWeighted(team_bg, 0.75, frame, 0.25, 0, frame)

    # Divider lines
    for div_x in [sb_x + team_w, sb_x + team_w + score_w,
                  sb_x + sb_w - team_w - score_w, sb_x + sb_w - team_w]:
        cv2.line(frame, (div_x, sb_y + 8), (div_x, sb_y + sb_h - 8), (55, 55, 65), 1)

    # Font sizes
    team_font_size = 52
    score_font_size = 72
    period_font_size = 36
    time_font_size = 32

    font_team = get_font('bold', team_font_size)
    font_score = get_font('bold', score_font_size)
    font_period = get_font('light', period_font_size)
    font_time = get_font('regular', time_font_size)

    center_y = sb_y + sb_h // 2

    # Home team name
    tw, th = get_text_size_pil(home_team, font_team)
    tx = sb_x + (team_w - tw) // 2
    ty = center_y - th // 2
    frame = draw_text_pil(frame, home_team, tx, ty, font_team, (230, 230, 230))

    # Home score
    sw, sh = get_text_size_pil(str(home_score), font_score)
    sx = sb_x + team_w + (score_w - sw) // 2
    sy = center_y - sh // 2
    frame = draw_text_pil(frame, str(home_score), sx, sy, font_score, (255, 255, 255))

    # Away score
    asw, ash = get_text_size_pil(str(away_score), font_score)
    asx = sb_x + sb_w - team_w - score_w + (score_w - asw) // 2
    asy = center_y - ash // 2
    frame = draw_text_pil(frame, str(away_score), asx, asy, font_score, (255, 255, 255))

    # Away team name
    atw, ath = get_text_size_pil(away_team, font_team)
    atx = sb_x + sb_w - team_w + (team_w - atw) // 2
    aty = center_y - ath // 2
    frame = draw_text_pil(frame, away_team, atx, aty, font_team, (230, 230, 230))

    # Center section
    center_x = sb_x + team_w + score_w
    
    # Period
    pw, ph = get_text_size_pil(period, font_period)
    px = center_x + (center_w - pw) // 2
    py = center_y - ph - int(sb_h * 0.06)
    frame = draw_text_pil(frame, period, px, py, font_period, (160, 160, 160))

    # Game time
    tmw, tmh = get_text_size_pil(game_time, font_time)
    tmx = center_x + (center_w - tmw) // 2
    tmy = center_y + int(sb_h * 0.06)
    frame = draw_text_pil(frame, game_time, tmx, tmy, font_time, (200, 200, 200))

    # Ticker bar — same width as scoreboard
    if ticker_text:
        ticker_h = int(sb_h * 0.30)
        ticker_y = sb_y + sb_h
        ticker_overlay = frame.copy()
        cv2.rectangle(ticker_overlay, (sb_x, ticker_y), (sb_x + sb_w, ticker_y + ticker_h), (10, 10, 14), -1)
        cv2.addWeighted(ticker_overlay, 0.88, frame, 0.12, 0, frame)
        cv2.rectangle(frame, (sb_x, ticker_y), (sb_x + 4, ticker_y + ticker_h), (255, 140, 0), -1)
        ticker_font = get_font('light', max(8, int(ticker_h * 0.42)))
        tw, th = get_text_size_pil(ticker_text, ticker_font)
        frame = draw_text_pil(frame, ticker_text, sb_x + 12,
                              ticker_y + (ticker_h - th) // 2, ticker_font, (190, 190, 190))

    # TM Ventures watermark
    wm_font = get_font('light', max(8, int(h * 0.012)))
    wm_text = 'POWERED BY TM VENTURES'
    wmw, wmh = get_text_size_pil(wm_text, wm_font)
    frame = draw_text_pil(frame, wm_text, w - wmw - 10, h - wmh - 8, wm_font, (90, 90, 90))

    return frame


def draw_lower_third(frame, player_name='', stat_line='', team_color=(255, 140, 0)):
    h, w = frame.shape[:2]

    lt_h = int(h * 0.09)
    lt_y = int(h * 0.80)
    lt_w = int(w * 0.78)

    shadow = frame.copy()
    cv2.rectangle(shadow, (0, lt_y - 2), (lt_w + 4, lt_y + lt_h + 2), (0, 0, 0), -1)
    cv2.addWeighted(shadow, 0.35, frame, 0.65, 0, frame)

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, lt_y), (lt_w, lt_y + lt_h), (15, 15, 20), -1)
    cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

    cv2.rectangle(frame, (0, lt_y), (6, lt_y + lt_h), team_color, -1)
    cv2.rectangle(frame, (0, lt_y), (lt_w, lt_y + 2), team_color, -1)

    if player_name:
        name_font = get_font('bold', max(10, int(lt_h * 0.38)))
        nw, nh = get_text_size_pil(player_name.upper(), name_font)
        frame = draw_text_pil(frame, player_name.upper(), 16,
                              lt_y + int(lt_h * 0.18), name_font, (255, 255, 255))

    if stat_line:
        stat_font = get_font('light', max(8, int(lt_h * 0.26)))
        frame = draw_text_pil(frame, stat_line, 16,
                              lt_y + int(lt_h * 0.60), stat_font, (180, 180, 180))

    return frame


def draw_highlight_label(frame, sport='basketball', hype_score=0):
    h, w = frame.shape[:2]

    labels = {
        'basketball': {80: '3 POINTER', 70: 'SLAM DUNK', 60: 'FAST BREAK', 0: 'HIGHLIGHT'},
        'soccer': {80: 'GOOOAL!', 70: 'GREAT SAVE', 60: 'BIG CHANCE', 0: 'HIGHLIGHT'},
        'mma': {80: 'KNOCKOUT!', 70: 'SUBMISSION', 60: 'BIG COMBO', 0: 'HIGHLIGHT'},
        'darts': {80: '180!', 70: 'CHECKOUT!', 60: 'BIG FINISH', 0: 'HIGHLIGHT'},
        'football': {80: 'TOUCHDOWN!', 70: 'BIG PLAY', 60: 'FIRST DOWN', 0: 'HIGHLIGHT'},
        'baseball': {80: 'HOME RUN!', 70: 'STRIKEOUT!', 60: 'BIG HIT', 0: 'HIGHLIGHT'},
        'volleyball': {80: 'ACE!', 70: 'SPIKE!', 60: 'BIG BLOCK', 0: 'HIGHLIGHT'},
        'cricket': {80: 'SIX!', 70: 'WICKET!', 60: 'BOUNDARY!', 0: 'HIGHLIGHT'},
        'tennis': {80: 'ACE!', 70: 'WINNER!', 60: 'BREAK POINT', 0: 'HIGHLIGHT'},
        'hockey': {80: 'GOAL!', 70: 'BIG SAVE', 60: 'POWER PLAY', 0: 'HIGHLIGHT'},
    }

    sport_labels = labels.get(sport, {0: 'HIGHLIGHT'})
    label = 'HIGHLIGHT'
    for threshold in sorted(sport_labels.keys(), reverse=True):
        if hype_score >= threshold:
            label = sport_labels[threshold]
            break

    label_font = get_font('bold', max(8, int(h * 0.020)))
    lw, lh = get_text_size_pil(label, label_font)
    lx = w - lw - 12
    ly = h - lh - 12

    # Shadow
    frame = draw_text_pil(frame, label, lx + 1, ly + 1, label_font, (0, 0, 0))
    # Label
    frame = draw_text_pil(frame, label, lx, ly, label_font, (255, 140, 0))

    return frame


def apply_overlay_to_clip(clip_path, output_path, overlay_config):
    cap = cv2.VideoCapture(clip_path)

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if width == 0 or height == 0:
        print('Skipping corrupt file: ' + os.path.basename(clip_path))
        cap.release()
        return None

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    home_team = overlay_config.get('home_team', 'HOME')
    away_team = overlay_config.get('away_team', 'AWAY')
    home_score = overlay_config.get('home_score', 0)
    away_score = overlay_config.get('away_score', 0)
    game_time = overlay_config.get('game_time', '00:00')
    period = overlay_config.get('period', 'Q1')
    ticker_text = overlay_config.get('ticker_text', '')
    sport = overlay_config.get('sport', 'basketball')
    hype_score = overlay_config.get('hype_score', 0)
    team_color = tuple(overlay_config.get('team_color', [255, 140, 0]))
    player_name = overlay_config.get('player_name', '')
    stat_line = overlay_config.get('stat_line', '')
    show_scoreboard = overlay_config.get('show_scoreboard', True)
    show_lower_third = overlay_config.get('show_lower_third', bool(player_name))
    show_label = overlay_config.get('show_label', True)

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if show_scoreboard:
            frame = draw_scoreboard(frame, home_team, away_team,
                                   home_score, away_score, game_time, period,
                                   ticker_text, sport)

        if show_lower_third and player_name:
            frame = draw_lower_third(frame, player_name, stat_line, team_color)

        if show_label:
            frame = draw_highlight_label(frame, sport, hype_score)

        out.write(frame)
        frame_count += 1

    cap.release()
    out.release()

    if frame_count > 0:
        print('Overlay applied: ' + os.path.basename(output_path) + ' (' + str(frame_count) + ' frames)')

    return output_path


def apply_overlays_to_folder(output_dir, overlay_config):
    clips = sorted([f for f in glob.glob(os.path.join(output_dir, 'highlight_*_vertical.mp4'))
                   if '_overlay' not in f])
    clips += sorted([f for f in glob.glob(os.path.join(output_dir, 'highlight_*_horizontal.mp4'))
                    if '_overlay' not in f])

    reel = os.path.join(output_dir, 'highlight_reel_horizontal.mp4')
    if os.path.exists(reel):
        clips.append(reel)

    print('========================================')
    print('   TM VENTURES - BROADCAST OVERLAY')
    print('========================================')
    print('Applying overlays to ' + str(len(clips)) + ' clips...\n')

    overlaid = []
    for clip in clips:
        name = Path(clip).stem
        output_path = os.path.join(output_dir, name + '_overlay.mp4')
        result = apply_overlay_to_clip(clip, output_path, overlay_config)
        if result:
            overlaid.append(result)

    print('\nDone. ' + str(len(overlaid)) + ' clips with broadcast overlay saved.')
    return overlaid


if __name__ == '__main__':
    config = {
        'home_team': 'LAL',
        'away_team': 'CHI',
        'home_score': 54,
        'away_score': 48,
        'game_time': '4:22',
        'period': 'Q3',
        'ticker_text': 'JAMES 24 PTS  8 REB  6 AST  |  TEAM FOULS: 12  |  TIMEOUTS: 2',
        'sport': 'basketball',
        'hype_score': 75,
        'team_color': [85, 37, 130],
        'player_name': 'LeBron James',
        'stat_line': '24 PTS  |  8 REB  |  6 AST  |  +12',
        'show_scoreboard': True,
        'show_lower_third': True,
        'show_label': True
    }

    output_dir = os.path.expanduser('~/highlight-editor/output')
    apply_overlays_to_folder(output_dir, config)
