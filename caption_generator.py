import anthropic
import os


def generate_captions(sport, timestamps, scores, clip_duration=14):
    client = anthropic.Anthropic()

    highlights_text = ""
    for i, (timestamp, score) in enumerate(zip(timestamps, scores)):
        minutes = int(timestamp // 60)
        seconds = int(timestamp % 60)
        flame = "🔥" if score >= 70 else ""
        highlights_text += f"Clip {i+1}: {minutes}:{str(seconds).zfill(2)} — Hype Score: {score} {flame}\n"

    prompt = f"""You are a social media expert specializing in sports content. 
    
I have {len(timestamps)} highlight clips from a {sport} game. Each clip is {clip_duration} seconds long.

Here are the clips with their hype scores:
{highlights_text}

Generate social media captions and hashtags for each clip. For each clip provide:
1. An Instagram/TikTok caption (punchy, engaging, under 150 characters)
2. A Twitter/X caption (under 280 characters, more conversational)
3. 8-10 relevant hashtags specific to {sport}

Format your response exactly like this for each clip:
CLIP 1:
INSTAGRAM: [caption]
TWITTER: [caption]
HASHTAGS: [hashtags]

CLIP 2:
INSTAGRAM: [caption]
TWITTER: [caption]
HASHTAGS: [hashtags]

Keep the tone energetic and authentic. Reference the hype score to gauge how exciting each moment was."""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text


def parse_captions(caption_text):
    clips = {}
    current_clip = None
    lines = caption_text.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if 'CLIP' in line.upper() and ':' in line and 'INSTAGRAM' not in line.upper() and 'TWITTER' not in line.upper() and 'HASHTAGS' not in line.upper():
            try:
                num = int(line.upper().replace('CLIP', '').replace(':', '').strip())
                current_clip = num
                clips[current_clip] = {}
            except:
                pass
        elif line.upper().startswith('INSTAGRAM:') and current_clip:
            clips[current_clip]['instagram'] = line[10:].strip().strip('"').strip("'")
        elif line.upper().startswith('TWITTER:') and current_clip:
            clips[current_clip]['twitter'] = line[8:].strip().strip('"').strip("'")
        elif line.upper().startswith('HASHTAGS:') and current_clip:
            clips[current_clip]['hashtags'] = line[9:].strip().strip('"').strip("'")

    return clips


def generate_and_save_captions(sport, highlights, clip_duration=14, output_dir=None):
    if output_dir is None:
        output_dir = os.path.expanduser('~/highlight-editor/output')

    timestamps = [h['timestamp'] for h in highlights]
    scores = [h['score'] for h in highlights]

    print('Generating AI captions and hashtags...')
    caption_text = generate_captions(sport, timestamps, scores, clip_duration)
    captions = parse_captions(caption_text)

    output_file = os.path.join(output_dir, 'captions.txt')
    with open(output_file, 'w') as f:
        f.write('AI GENERATED CAPTIONS AND HASHTAGS\n')
        f.write('=' * 40 + '\n\n')
        for clip_num, data in captions.items():
            minutes = int(timestamps[clip_num-1] // 60)
            seconds = int(timestamps[clip_num-1] % 60)
            f.write(f'CLIP {clip_num} — {minutes}:{str(seconds).zfill(2)}\n')
            f.write(f'Score: {scores[clip_num-1]}\n\n')
            f.write(f'INSTAGRAM:\n{data.get("instagram", "")}\n\n')
            f.write(f'TWITTER:\n{data.get("twitter", "")}\n\n')
            f.write(f'HASHTAGS:\n{data.get("hashtags", "")}\n\n')
            f.write('-' * 40 + '\n\n')

    print('Captions saved to: ' + output_file)
    return captions