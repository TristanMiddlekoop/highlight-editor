import whisper
import cv2
import subprocess
import os
import glob


def draw_caption(frame, text, video_width, video_height, font_size=1.0, position=0.82):
    font = cv2.FONT_HERSHEY_DUPLEX
    font_scale = (video_width / 800) * font_size
    thickness = max(2, int(font_scale * 2))
    max_width = int(video_width * 0.85)
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = ' '.join(current + [word])
        (w, _), _ = cv2.getTextSize(test, font, font_scale, thickness)
        if w <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(' '.join(current))
            current = [word]
    if current:
        lines.append(' '.join(current))
    line_height = int(font_scale * 45)
    total_height = len(lines) * line_height
    y_start = int(video_height * position) - total_height
    for i, line in enumerate(lines):
        y = y_start + i * line_height
        (w, h), _ = cv2.getTextSize(line, font, font_scale, thickness)
        x = (video_width - w) // 2
        cv2.putText(frame, line, (x+2, y+2), font, font_scale, (0, 0, 0), thickness+2)
        cv2.putText(frame, line, (x, y), font, font_scale, (255, 255, 255), thickness)
    return frame


def build_word_chunks(segments, chunk_size=4):
    all_words = []
    for seg in segments:
        if "words" in seg:
            for word in seg["words"]:
                all_words.append({
                    "word": word["word"].strip(),
                    "start": float(word["start"]),
                    "end": float(word["end"])
                })
    chunks = []
    for i in range(0, len(all_words), chunk_size):
        group = all_words[i:i+chunk_size]
        chunks.append({
            "text": " ".join(w["word"] for w in group),
            "start": group[0]["start"],
            "end": group[-1]["end"]
        })
    return chunks


def add_captions(clip_path, output_path, font_size=1.0, position=0.82):
    print("Transcribing: " + os.path.basename(clip_path))
    model = whisper.load_model("base")
    result = model.transcribe(clip_path, word_timestamps=True)
    chunks = build_word_chunks(result["segments"], chunk_size=4)

    cap = cv2.VideoCapture(clip_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    tmp_video = output_path.replace(".mp4", "_tmp.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(tmp_video, fourcc, fps, (width, height))

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        current_time = frame_idx / fps
        caption_text = ""
        for chunk in chunks:
            if chunk["start"] <= current_time < chunk["end"]:
                caption_text = chunk["text"]
                break
        if caption_text:
            frame = draw_caption(frame, caption_text, width, height, font_size, position)
        out.write(frame)
        frame_idx += 1

    cap.release()
    out.release()

    command = [
        "ffmpeg", "-i", tmp_video, "-i", clip_path,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-c:a", "aac", "-y", output_path
    ]
    subprocess.run(command, capture_output=True)
    os.remove(tmp_video)
    print("Captions added: " + os.path.basename(output_path))

def caption_all_clips(output_dir, format="vertical", new_clips_only=None, font_size=1.0, position=0.82):
    if isinstance(output_dir, str) and output_dir.startswith("~"):
        output_dir = os.path.expanduser(output_dir)
    if new_clips_only:
        clips = [os.path.join(output_dir, c) for c in new_clips_only]
        clips = [c for c in clips if os.path.exists(c)]
    else:
        clips = glob.glob(os.path.join(output_dir, "highlight_*_" + format + ".mp4"))
        clips = [c for c in clips if "_captioned" not in c]
    if not clips:
        print("No clips found to caption")
        return
    print("Adding captions to " + str(len(clips)) + " clips...")
    for clip in clips:
        captioned = clip.replace("_" + format + ".mp4", "_" + format + "_captioned.mp4")
        add_captions(clip, captioned, font_size, position)
    print("Done. Captioned clips saved to output folder")
