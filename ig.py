import io
import os
import glob
import mimetypes
import tempfile
import zipfile

import streamlit as st
from yt_dlp import YoutubeDL

st.set_page_config(page_title="Insta Downloader", page_icon="📥", layout="centered")
st.title("📥 Instagram Downloader")
st.caption("Paste an Instagram post/reel URL and download the media you have permission to save.")

with st.expander("Read this first", expanded=False):
    st.markdown(
        """
        *Disclaimer*: This tool is for personal/educational use. Only download content if you
        are the owner, have explicit permission, or the license allows it. Instagram's terms of service
        may restrict downloading. Proceed at your own responsibility.
        """
    )

url = st.text_input("Instagram URL", placeholder="https://www.instagram.com/reel/… or https://www.instagram.com/p/…")
confirm = st.checkbox("I confirm I have permission to download this content.")

# Optional settings
col1, col2 = st.columns(2)
with col1:
    format_note = st.selectbox(
        "Preferred format (videos)",
        options=["mp4", "best"],
        index=0,
        help="mp4 tries to pick mp4 video, best lets yt-dlp decide automatically."
    )
with col2:
    keep_audio_only = st.checkbox("Audio only (if available)")


def _make_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for fp in files:
            zf.write(fp, arcname=os.path.basename(fp))
    buf.seek(0)
    return buf


def _mime_for(path):
    mt, _ = mimetypes.guess_type(path)
    return mt or "application/octet-stream"


if st.button("Download", type="primary"):
    if not url.strip():
        st.error("Please paste an Instagram URL.")
        st.stop()
    if "instagram.com" not in url:
        st.error("This doesn't look like an Instagram link.")
        st.stop()
    if not confirm:
        st.warning("You must confirm permission to proceed.")
        st.stop()

    ydl_opts = {
        "quiet": True,
        "noprogress": True,
        "restrictfilenames": True,
        # ❌ ffmpeg dependency avoid -> no merge_output_format
    }

    if keep_audio_only:
        # audio only option
        ydl_opts.update({
            "format": "bestaudio[ext=mp3]/bestaudio",
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
            ],
        })
    else:
        # fallback for video + image without requiring ffmpeg merge
        if format_note == "mp4":
            ydl_opts.update({
                "format": "best[ext=mp4]/bestimage/best"
            })
        else:
            ydl_opts.update({
                "format": "best/bestimage"
            })

    with tempfile.TemporaryDirectory() as tmpdir:
        ydl_opts["outtmpl"] = os.path.join(tmpdir, "%(title).200B.%(id)s.%(ext)s")

        status = st.status("Fetching media…", expanded=True)
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            status.update(label="Download complete.", state="complete")

            files = glob.glob(os.path.join(tmpdir, "*"))
            if not files:
                st.error("No files were produced. The link may be unsupported or private.")
                st.stop()

            if len(files) == 1:
                fp = files[0]
                fname = os.path.basename(fp)
                with open(fp, "rb") as f:
                    data = f.read()
                st.success("Ready! Click below to save.")
                st.download_button(
                    label=f"⬇️ Download {fname}",
                    data=data,
                    file_name=fname,
                    mime=_mime_for(fp),
                )
            else:
                buf = _make_zip(files)
                st.success("Multiple files found (album/carousel). Download the ZIP.")
                st.download_button(
                    label="⬇️ Download ZIP",
                    data=buf,
                    file_name="instagram_media.zip",
                    mime="application/zip",
                )

            # Show a tiny info panel
            with st.expander("Details"):
                if isinstance(info, dict):
                    title = info.get("title") or "—"
                    uploader = info.get("uploader") or info.get("uploader_id") or "—"
                    duration = info.get("duration")
                    webpage_url = info.get("webpage_url") or url
                    st.write({
                        "title": title,
                        "uploader": uploader,
                        "duration_seconds": duration,
                        "source": webpage_url,
                    })

        except Exception as e:
            status.update(label="Failed.", state="error")
            st.exception(e)
            st.info(
                "If this is a private link or requires login, the download may fail. Try a public post/reel."
            )
