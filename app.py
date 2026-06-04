import anthropic
import streamlit as st
import os
import sys
import glob
import shutil
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('ANTHROPIC_API_KEY', os.environ.get('ANTHROPIC_API_KEY', ''))

from detector import find_highlights, SPORT_PRESETS
from cutter import cut_highlights
from exporter import stitch_highlights
from captions import caption_all_clips
from caption_generator import generate_and_save_captions, generate_captions, parse_captions

st.set_page_config(page_title="AI Highlight Editor", page_icon="🎬", layout="wide")

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
    use_preview = st.toggle("Preview Before Download", value=True)

st.divider()

uploaded_file = st.file_uploader("Upload your video", type=["mp4", "mov", "webm", "avi", "mkv"])

if uploaded_file:

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

            ai_captions = {}
            st.write("🤖 Generating AI captions and hashtags...")
            try:
                caption_text = generate_captions(sport, timestamps, [h['score'] for h in highlights], SPORT_PRESETS[sport]['clip_duration'])
                ai_captions = parse_captions(caption_text)
                st.write("✅ Generated captions for " + str(len(ai_captions)) + " clips")
            except Exception as e:
                st.write("⚠️ Caption generation failed: " + str(e))

            status.update(label="✅ Done!", state="complete")

        st.session_state['output_dir'] = output_dir
        st.session_state['highlights'] = highlights
        st.session_state['ai_captions'] = ai_captions
        st.session_state['processed'] = True

    if st.session_state.get('processed'):
        output_dir = st.session_state['output_dir']
        highlights = st.session_state['highlights']
        ai_captions = st.session_state['ai_captions']
        st.write("DEBUG: " + str(len(ai_captions)) + " caption sets stored")

        st.divider()

        if use_preview:
            st.subheader("👀 Preview + Approve Clips")
            st.markdown("Review each clip before downloading. Edit captions if needed.")

            approved_clips = []
            all_vertical = sorted(glob.glob(os.path.join(output_dir, "highlight_*_vertical.mp4")))

            for i, clip_path in enumerate(all_vertical):
                clip_name = os.path.basename(clip_path)
                clip_num = i + 1

                with st.expander("Clip " + str(clip_num) + " — " + clip_name, expanded=True):
                    col1, col2 = st.columns([1, 1])

                    with col1:
                        st.video(clip_path)
                        minutes = int(highlights[i]['timestamp'] // 60) if i < len(highlights) else 0
                        seconds = int(highlights[i]['timestamp'] % 60) if i < len(highlights) else 0
                        score = highlights[i]['score'] if i < len(highlights) else 0
                        flame = "🔥" if score >= 70 else ""
                        st.caption("Timestamp: " + str(minutes) + ":" + str(seconds).zfill(2) + " | Score: " + str(score) + " " + flame)

                    with col2:
                        if ai_captions and clip_num in ai_captions:
                            instagram = st.text_area("Instagram Caption", value=ai_captions[clip_num].get('instagram', ''), key="ig_" + str(clip_num))
                            twitter = st.text_area("Twitter/X Caption", value=ai_captions[clip_num].get('twitter', ''), key="tw_" + str(clip_num))
                            hashtags = st.text_area("Hashtags", value=ai_captions[clip_num].get('hashtags', ''), key="ht_" + str(clip_num))
                        else:
                            st.info("Enable AI Caption Generator for captions")

                    approve = st.checkbox("✅ Approve this clip", value=True, key="approve_" + str(clip_num))
                    if approve:
                        approved_clips.append(clip_path)

            st.divider()
            st.write("**" + str(len(approved_clips)) + " of " + str(len(all_vertical)) + " clips approved**")

            if st.button("⬇️ Download Approved Clips", type="primary"):
                for clip_path in approved_clips:
                    clip_name = os.path.basename(clip_path)
                    with open(clip_path, "rb") as f:
                        st.download_button(
                            label="⬇️ " + clip_name,
                            data=f,
                            file_name=clip_name,
                            mime="video/mp4",
                            key="dl_" + clip_name
                        )

                reel = os.path.join(output_dir, "highlight_reel_horizontal.mp4")
                if os.path.exists(reel):
                    with open(reel, "rb") as f:
                        st.download_button(
                            label="⬇️ highlight_reel_horizontal.mp4",
                            data=f,
                            file_name="highlight_reel_horizontal.mp4",
                            mime="video/mp4",
                            key="dl_reel"
                        )

        else:
            st.subheader("📥 Download Your Clips")
            all_clips = glob.glob(os.path.join(output_dir, "*.mp4"))
            for clip in sorted(all_clips):
                clip_name = os.path.basename(clip)
                with open(clip, "rb") as f:
                    st.download_button(
                        label="⬇️ " + clip_name,
                        data=f,
                        file_name=clip_name,
                        mime="video/mp4",
                        key="dl_" + clip_name
                    )