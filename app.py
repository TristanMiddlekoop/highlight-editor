import streamlit as st
import os
import sys
import glob
import shutil
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from detector import find_highlights, SPORT_PRESETS
from cutter import cut_highlights
from exporter import stitch_highlights
from captions import caption_all_clips
from caption_generator import generate_and_save_captions

st.set_page_config(page_title="AI Highlight Editor", page_icon="🎬", layout="centered")

st.title("🎬 AI Sports Highlight Editor")
st.markdown("Upload a sports video and get highlight clips automatically.")

with st.sidebar:
    st.header("⚙️ Settings")
    sport = st.selectbox("Sport", list(SPORT_PRESETS.keys()), index=0)
    mode = st.radio("Output Mode", ["both", "short", "long"], index=0)
    top_n = st.slider("Number of Clips", min_value=1, max_value=15, value=5)
    use_captions = st.toggle("Auto Captions", value=False)
    if use_captions:
        font_size = st.slider("Caption Font Size", 0.5, 2.0, 1.3)
        position = st.slider("Caption Position", 0.5, 0.98, 0.88)
    else:
        font_size = 1.3
        position = 0.88
    use_ai_captions = st.toggle("AI Caption Generator", value=True)

st.divider()

uploaded_file = st.file_uploader("Upload your video", type=["mp4", "mov", "webm", "avi", "mkv"])

if uploaded_file:
    st.video(uploaded_file)

    if st.button("🚀 Process Highlights", type="primary"):
        tmp_dir = tempfile.mkdtemp()
        output_dir = os.path.join(tmp_dir, "output")
        os.makedirs(output_dir)

        video_path = os.path.join(tmp_dir, uploaded_file.name)
        with open(video_path, "wb") as f:
            f.write(uploaded_file.read())

        with st.status("Processing your video...", expanded=True) as status:
            st.write("🔍 Detecting highlights...")
            highlights = find_highlights(video_path, sensitivity=SPORT_PRESETS[sport]['sensitivity'], min_gap=SPORT_PRESETS[sport]['min_gap'])
            highlights = sorted(highlights, key=lambda x: x['score'], reverse=True)
            if len(highlights) > top_n:
                highlights = highlights[:top_n]
            highlights = sorted(highlights, key=lambda x: x['timestamp'])
            timestamps = [h['timestamp'] for h in highlights]

            st.write("Found " + str(len(highlights)) + " highlights")
            for h in highlights:
                minutes = int(h['timestamp'] // 60)
                seconds = int(h['timestamp'] % 60)
                flame = "🔥" if h['score'] >= 70 else ""
                st.write("  → " + str(minutes) + ":" + str(seconds).zfill(2) + " — Score: " + str(h['score']) + " " + flame)

            if mode in ("short", "both"):
                st.write("✂️ Cutting short form clips...")
                cut_highlights(video_path, timestamps, clip_duration=SPORT_PRESETS[sport]['clip_duration'], format='vertical', output_dir=output_dir)
                if use_captions:
                    st.write("💬 Adding captions...")
                    caption_all_clips(output_dir, format='vertical', font_size=font_size, position=position)

            if mode in ("long", "both"):
                st.write("🎞️ Stitching long form reel...")
                cut_highlights(video_path, timestamps, clip_duration=SPORT_PRESETS[sport]['clip_duration'], format='horizontal', output_dir=output_dir)
                stitch_highlights(output_dir, final_output_name='highlight_reel_horizontal.mp4')

            if use_ai_captions:
                st.write("🤖 Generating AI captions and hashtags...")
                generate_and_save_captions(sport, highlights, clip_duration=SPORT_PRESETS[sport]['clip_duration'], output_dir=output_dir)

            status.update(label="✅ Done!", state="complete")

        st.divider()
        st.subheader("📥 Download Your Clips")

        all_clips = glob.glob(os.path.join(output_dir, "*.mp4"))
        for clip in sorted(all_clips):
            clip_name = os.path.basename(clip)
            with open(clip, "rb") as f:
                st.download_button(
                    label="⬇️ " + clip_name,
                    data=f,
                    file_name=clip_name,
                    mime="video/mp4"
                )

        captions_file = os.path.join(output_dir, "captions.txt")
        if os.path.exists(captions_file):
            with open(captions_file, "r") as f:
                st.divider()
                st.subheader("📝 AI Generated Captions")
                st.text(f.read())
                st.download_button(
                    label="⬇️ Download captions.txt",
                    data=open(captions_file).read(),
                    file_name="captions.txt",
                    mime="text/plain"
                )

        shutil.rmtree(tmp_dir)