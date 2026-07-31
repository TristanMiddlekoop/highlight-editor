
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
from caption_generator import generate_captions, parse_captions
from scheduler import add_to_queue, view_queue, set_posting_times, load_schedule
from analytics import get_dashboard, load_analytics

st.set_page_config(page_title="AI Highlight Editor", page_icon="🎬", layout="wide")

st.title("🎬 AI Sports Highlight Editor")
st.markdown("Upload a sports video and get highlight clips automatically.")

for key, default in [('processed', False), ('ai_captions', {}), ('highlights', []), ('output_dir', ''), ('processing', False)]:
    if key not in st.session_state:
        st.session_state[key] = default

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
    use_preview = st.toggle("Preview Before Download", value=True)

st.divider()

st.subheader("📁 Select Video")
input_method = st.radio("Input method", ["Upload file", "Local file path"], horizontal=True)

video_ready = False
video_source = None

if input_method == "Upload file":
    uploaded_file = st.file_uploader("Upload your video", type=["mp4", "mov", "webm", "avi", "mkv"])
    if uploaded_file:
        video_ready = True
        video_source = ("upload", uploaded_file)
else:
    local_path = st.text_input("Enter full path to video", placeholder="/Users/tristanmiddlekoop/highlight-editor/test_videos/nba_test.webm")
    if local_path and os.path.exists(os.path.expanduser(local_path)):
        video_ready = True
        video_source = ("local", local_path)
        st.success("✅ File found: " + os.path.basename(local_path))
    elif local_path:
        st.error("File not found: " + local_path)

if video_ready and not st.session_state.processing:
    if st.button("🚀 Process Highlights", type="primary"):
        st.session_state.processing = True
        st.session_state.processed = False

        output_dir = os.path.expanduser('~/highlight-editor/output')
        os.makedirs(output_dir, exist_ok=True)

        if video_source[0] == "upload":
            tmp_dir = tempfile.mkdtemp()
            video_path = os.path.join(tmp_dir, video_source[1].name)
            with open(video_path, "wb") as f:
                f.write(video_source[1].read())
        else:
            tmp_dir = None
            video_path = os.path.expanduser(video_source[1])

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

            st.write("🤖 Generating AI captions and hashtags...")
            try:
                caption_text = generate_captions(sport, timestamps, [h['score'] for h in highlights], SPORT_PRESETS[sport]['clip_duration'])
                ai_captions = parse_captions(caption_text)
                st.write("✅ Captions generated for " + str(len(ai_captions)) + " clips")
            except Exception as e:
                ai_captions = {}
                st.write("⚠️ Caption generation failed: " + str(e))

            status.update(label="✅ Done!", state="complete")

        st.session_state.output_dir = output_dir
        st.session_state.highlights = highlights
        st.session_state.ai_captions = ai_captions
        st.session_state.processed = True
        st.session_state.processing = False

        if tmp_dir:
            shutil.rmtree(tmp_dir)

if st.session_state.processed:
    output_dir = st.session_state.output_dir
    highlights = st.session_state.highlights
    ai_captions = st.session_state.ai_captions

    st.divider()

    if use_preview:
        st.subheader("👀 Preview + Approve Clips")
        st.markdown("Review each clip before downloading. Edit captions if needed.")

        approved_clips = []
        all_vertical = sorted([f for f in glob.glob(os.path.join(output_dir, "highlight_*_vertical.mp4")) if "_captioned" not in f])

        for i, clip_path in enumerate(all_vertical):
            clip_name = os.path.basename(clip_path)
            clip_num = i + 1

            with st.expander("Clip " + str(clip_num) + " — " + clip_name, expanded=True):
                col1, col2 = st.columns([1, 1])

                with col1:
                    st.video(clip_path)
                    if i < len(highlights):
                        minutes = int(highlights[i]['timestamp'] // 60)
                        seconds = int(highlights[i]['timestamp'] % 60)
                        score = highlights[i]['score']
                        flame = "🔥" if score >= 70 else ""
                        st.caption("Timestamp: " + str(minutes) + ":" + str(seconds).zfill(2) + " | Score: " + str(score) + " " + flame)

                with col2:
                    if ai_captions and clip_num in ai_captions:
                        st.text_area("Instagram Caption", value=ai_captions[clip_num].get('instagram', ''), key="ig_" + str(clip_num))
                        st.text_area("Twitter/X Caption", value=ai_captions[clip_num].get('twitter', ''), key="tw_" + str(clip_num))
                        st.text_area("Hashtags", value=ai_captions[clip_num].get('hashtags', ''), key="ht_" + str(clip_num))
                    else:
                        st.info("No AI captions available")

                approve = st.checkbox("✅ Approve this clip", value=True, key="approve_" + str(clip_num))
                if approve:
                    approved_clips.append(clip_path)

        st.divider()
        st.write("**" + str(len(approved_clips)) + " of " + str(len(all_vertical)) + " clips approved**")

        col_dl, col_sched = st.columns([1, 1])

        with col_dl:
            if st.button("⬇️ Download Approved Clips", type="primary"):
                for clip_path in approved_clips:
                    clip_name = os.path.basename(clip_path)
                    with open(clip_path, "rb") as f:
                        st.download_button(label="⬇️ " + clip_name, data=f, file_name=clip_name, mime="video/mp4", key="dl_" + clip_name)
                reel = os.path.join(output_dir, "highlight_reel_horizontal.mp4")
                if os.path.exists(reel):
                    with open(reel, "rb") as f:
                        st.download_button(label="⬇️ highlight_reel_horizontal.mp4", data=f, file_name="highlight_reel_horizontal.mp4", mime="video/mp4", key="dl_reel")

        with col_sched:
            st.subheader("📅 Schedule Posts")
            platforms = st.multiselect("Platforms", ["instagram", "tiktok", "twitter", "youtube"], default=["instagram"])
            if st.button("📅 Add Approved to Schedule", type="secondary"):
                schedule = load_schedule()
                if not schedule.get('posting_times'):
                    set_posting_times(['09:00', '12:00', '18:00'])
                added = 0
                for i, clip_path in enumerate(approved_clips):
                    clip_num = i + 1
                    caption = ai_captions.get(clip_num, {}).get('instagram', '')
                    hashtags = ai_captions.get(clip_num, {}).get('hashtags', '')
                    for platform in platforms:
                        add_to_queue(clip_path, platform, caption, hashtags)
                        added += 1
                st.success("✅ Added " + str(added) + " posts to schedule!")
                st.json(load_schedule()['queue'][-added:])



                st.divider()
            st.subheader("📋 Current Queue")
            schedule = load_schedule()
            queue = schedule.get('queue', [])
            if queue:
                for item in sorted(queue, key=lambda x: x['scheduled_time']):
                    status_icon = "✅" if item['status'] == 'posted' else "🕐"
                    st.write(status_icon + " **" + item['scheduled_time'] + "** | " + item['platform'].upper() + " | " + os.path.basename(item['clip_path']))
                    st.caption(item['caption'][:80] + "...")
            else:
                st.info("No posts queued yet")



    

    else:
        st.subheader("📥 Download Your Clips")
        all_clips = glob.glob(os.path.join(output_dir, "*.mp4"))
        for clip in sorted(all_clips):
            clip_name = os.path.basename(clip)
            with open(clip, "rb") as f:
                st.download_button(label="⬇️ " + clip_name, data=f, file_name=clip_name, mime="video/mp4", key="dl_" + clip_name)
                st.divider()
st.subheader("📊 Analytics Dashboard")

analytics = load_analytics()
schedule = load_schedule()
queue = schedule.get('queue', [])

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Videos Processed", len(analytics.get('videos_processed', [])))

with col2:
    import glob
    output_dir = os.path.expanduser('~/highlight-editor/output')
    clips = glob.glob(os.path.join(output_dir, '*.mp4'))
    st.metric("Clips in Output", len(clips))

with col3:
    queued = len([p for p in queue if p['status'] == 'queued'])
    st.metric("Posts Queued", queued)

with col4:
    published = len([p for p in queue if p['status'] == 'posted'])
    st.metric("Posts Published", published + len(analytics.get('posts_published', [])))

sport_stats = analytics.get('sport_stats', {})
if sport_stats:
    st.subheader("🏆 By Sport")
    sport_cols = st.columns(len(sport_stats))
    for idx, (sport, stats) in enumerate(sport_stats.items()):
        with sport_cols[idx]:
            st.metric(sport.capitalize(), str(stats['videos']) + ' videos')

upcoming = [p for p in queue if p['status'] == 'queued']
if upcoming:
    st.subheader("🕐 Upcoming Posts")
    for post in sorted(upcoming, key=lambda x: x['scheduled_time'])[:5]:
        st.write("🕐 **" + post['scheduled_time'] + "** | " + post['platform'].upper() + " | " + os.path.basename(post['clip_path']))
