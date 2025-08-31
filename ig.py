import io
import os
import glob
import mimetypes
import tempfile
import zipfile

import streamlit as st
from yt_dlp import YoutubeDL, DownloadError

st.set_page_config(page_title="Insta Downloader", page_icon="📥", layout="centered")
st.title("📥 Instagram Downloader")
st.caption("Paste an Instagram post/reel URL and download the media you have permission to save.")


# ✅ Guide section for cookies
with st.expander("📑 How to get cookies.txt (for private/login-required posts)", expanded=False):
    st.markdown(
        """
        To download **private posts** or if Instagram blocks downloads, you need to provide your `cookies.txt`.

        ### Step-by-step:
        1. Open Instagram in your browser and **log in** to your account.
        2. Install this extension:
           - [Get cookies.txt (Chrome)](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc?utm_source=chatgpt.com)
           - [Get cookies.txt (Firefox)](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
        3. Once logged in, click the extension icon → click **Export**.
        4. Save the file as `cookies.txt` on your computer.
        5. Upload it below in the uploader box.
        6. Now the downloader will work for private posts / login required content.

        ⚠️ Note: Cookies expire after some time. If download stops working, repeat the steps to get a fresh cookies.txt.
        """
    )

# 👉 First upload cookies, then paste link
cookies_file = st.file_uploader("Upload cookies.txt (required for private posts/login)", type=["txt"])
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
    if not cookies_file:
        st.error("Please upload cookies.txt first.")
        st.stop()
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
    }

    if keep_audio_only:
        ydl_opts.update({
            "format": "bestaudio[ext=mp3]/bestaudio",
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
            ],
        })
    else:
        if format_note == "mp4":
            ydl_opts.update({
                "format": "best[ext=mp4]/best/bestimage"
            })
        else:
            ydl_opts.update({
                "format": "best/bestimage"
            })

    with tempfile.TemporaryDirectory() as tmpdir:
        ydl_opts["outtmpl"] = os.path.join(tmpdir, "%(title).200B.%(id)s.%(ext)s")

        # Save cookies.txt if uploaded
        cookies_path = os.path.join(tmpdir, "cookies.txt")
        with open(cookies_path, "wb") as f:
            f.write(cookies_file.getbuffer())
        ydl_opts["cookiefile"] = cookies_path

        status = st.status("Fetching media…", expanded=True)
        try:
            with YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=True)
                except DownloadError as e:
                    # 👇 Fallback if no video found, try image
                    if "No video formats found" in str(e):
                        ydl_opts["format"] = "bestimage"
                        with YoutubeDL(ydl_opts) as ydl2:
                            info = ydl2.extract_info(url, download=True)
                    else:
                        raise

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
                "If this is a private link, requires login, or Instagram blocked your request, "
                "try uploading your `cookies.txt` file (see instructions in the expander above)."
            )





























# import io
# import os
# import glob
# import mimetypes
# import tempfile
# import zipfile

# import streamlit as st
# from yt_dlp import YoutubeDL

# st.set_page_config(page_title="Insta Downloader", page_icon="📥", layout="centered")
# st.title("📥 Instagram Downloader")
# st.caption("Upload cookies first, then paste the Instagram post/reel URL to download.")

# with st.expander("📑 How to get cookies.txt", expanded=False):
#     st.markdown(
#         """
#         To download **private posts** or if Instagram blocks downloads, you need to provide your `cookies.txt`.

#         ### Step-by-step:
#         1. Open Instagram in your browser and **log in** to your account.
#         2. Install this extension:
#            - [Get cookies.txt (Chrome)](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
#            - [Get cookies.txt (Firefox)](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
#         3. Once logged in, click the extension icon → click **Export**.
#         4. Save the file as `cookies.txt` on your computer.
#         5. Upload it below first, before pasting the Instagram link.

#         ⚠️ Note: Cookies expire after some time. If download stops working, repeat the steps to get a fresh cookies.txt.
#         """
#     )

# # Step 1: Upload cookies first
# cookies_file = st.file_uploader("Step 1️⃣ Upload cookies.txt (required)", type=["txt"])

# if cookies_file:
#     st.success("✅ Cookies uploaded successfully. Now paste Instagram URL below.")
    
#     # Step 2: URL after cookies
#     url = st.text_input("Step 2️⃣ Instagram URL", placeholder="https://www.instagram.com/reel/… or /p/…")
#     confirm = st.checkbox("I confirm I have permission to download this content.")

#     # Extra options
#     col1, col2 = st.columns(2)
#     with col1:
#         format_note = st.selectbox(
#             "Preferred format (videos)",
#             options=["mp4", "best"],
#             index=0,
#         )
#     with col2:
#         keep_audio_only = st.checkbox("Audio only (if available)")

#     def _make_zip(files):
#         buf = io.BytesIO()
#         with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
#             for fp in files:
#                 zf.write(fp, arcname=os.path.basename(fp))
#         buf.seek(0)
#         return buf

#     def _mime_for(path):
#         mt, _ = mimetypes.guess_type(path)
#         return mt or "application/octet-stream"

#     if st.button("⬇️ Download", type="primary"):
#         if not url.strip():
#             st.error("Please paste an Instagram URL.")
#             st.stop()
#         if "instagram.com" not in url:
#             st.error("This doesn't look like an Instagram link.")
#             st.stop()
#         if not confirm:
#             st.warning("You must confirm permission to proceed.")
#             st.stop()

#         ydl_opts = {
#             "quiet": True,
#             "noprogress": True,
#             "restrictfilenames": True,
#             "format": "best/bestimage"
#         }

#         if keep_audio_only:
#             ydl_opts.update({
#                 "format": "bestaudio[ext=mp3]/bestaudio",
#                 "postprocessors": [
#                     {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
#                 ],
#             })
#         else:
#             if format_note == "mp4":
#                 ydl_opts.update({"format": "best[ext=mp4]/bestimage/best"})
#             else:
#                 ydl_opts.update({"format": "best/bestimage"})

#         with tempfile.TemporaryDirectory() as tmpdir:
#             ydl_opts["outtmpl"] = os.path.join(tmpdir, "%(title).200B.%(id)s.%(ext)s")

#             # Save cookies.txt
#             cookies_path = os.path.join(tmpdir, "cookies.txt")
#             with open(cookies_path, "wb") as f:
#                 f.write(cookies_file.getbuffer())
#             ydl_opts["cookiefile"] = cookies_path

#             status = st.status("Fetching media…", expanded=True)
#             try:
#                 with YoutubeDL(ydl_opts) as ydl:
#                     info = ydl.extract_info(url, download=True)

#                 status.update(label="Download complete.", state="complete")

#                 files = glob.glob(os.path.join(tmpdir, "*"))
#                 if not files:
#                     st.error("No files were produced. The link may be unsupported or private.")
#                     st.stop()

#                 if len(files) == 1:
#                     fp = files[0]
#                     fname = os.path.basename(fp)
#                     with open(fp, "rb") as f:
#                         data = f.read()
#                     st.success("Ready! Click below to save.")
#                     st.download_button(
#                         label=f"⬇️ Download {fname}",
#                         data=data,
#                         file_name=fname,
#                         mime=_mime_for(fp),
#                     )
#                 else:
#                     buf = _make_zip(files)
#                     st.success("Multiple files found (album/carousel). Download the ZIP.")
#                     st.download_button(
#                         label="⬇️ Download ZIP",
#                         data=buf,
#                         file_name="instagram_media.zip",
#                         mime="application/zip",
#                     )

#                 with st.expander("Details"):
#                     if isinstance(info, dict):
#                         title = info.get("title") or "—"
#                         uploader = info.get("uploader") or info.get("uploader_id") or "—"
#                         duration = info.get("duration")
#                         webpage_url = info.get("webpage_url") or url
#                         st.write({
#                             "title": title,
#                             "uploader": uploader,
#                             "duration_seconds": duration,
#                             "source": webpage_url,
#                         })

#             except Exception as e:
#                 status.update(label="Failed.", state="error")
#                 st.exception(e)
#                 st.info("If it fails, re-upload a fresh cookies.txt.")
# else:
#     st.warning("👆 Please upload your cookies.txt first to continue.")






























# import io
# import os
# import glob
# import mimetypes
# import tempfile
# import zipfile

# import streamlit as st
# from yt_dlp import YoutubeDL

# st.set_page_config(page_title="Insta Downloader", page_icon="📥", layout="centered")
# st.title("📥 Instagram Downloader")
# st.caption("Paste an Instagram post/reel URL and download the media you have permission to save.")

# with st.expander("Read this first", expanded=False):
#     st.markdown(
#         """
#         *Disclaimer*: This tool is for personal/educational use. Only download content if you
#         are the owner, have explicit permission, or the license allows it. Instagram's terms of service
#         may restrict downloading. Proceed at your own responsibility.
#         """
#     )

# # ✅ Guide section for cookies
# with st.expander("📑 How to get cookies.txt (for private/login-required posts)", expanded=False):
#     st.markdown(
#         """
#         To download **private posts** or if Instagram blocks downloads, you need to provide your `cookies.txt`.

#         ### Step-by-step:
#         1. Open Instagram in your browser and **log in** to your account.
#         2. Install this extension:
#            - [Get cookies.txt (Chrome)](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc?utm_source=chatgpt.com)
#            - [Get cookies.txt (Firefox)](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
#         3. Once logged in, click the extension icon → click **Export**.
#         4. Save the file as `cookies.txt` on your computer.
#         5. Upload it below in the uploader box.
#         6. Now the downloader will work for private posts / login required content.

#         ⚠️ Note: Cookies expire after some time. If download stops working, repeat the steps to get a fresh cookies.txt.
#         """
#     )

# url = st.text_input("Instagram URL", placeholder="https://www.instagram.com/reel/… or https://www.instagram.com/p/…")
# confirm = st.checkbox("I confirm I have permission to download this content.")

# # Upload cookies option
# cookies_file = st.file_uploader("Upload cookies.txt (optional, needed for private posts/login required)", type=["txt"])

# # Optional settings
# col1, col2 = st.columns(2)
# with col1:
#     format_note = st.selectbox(
#         "Preferred format (videos)",
#         options=["mp4", "best"],
#         index=0,
#         help="mp4 tries to pick mp4 video, best lets yt-dlp decide automatically."
#     )
# with col2:
#     keep_audio_only = st.checkbox("Audio only (if available)")


# def _make_zip(files):
#     buf = io.BytesIO()
#     with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
#         for fp in files:
#             zf.write(fp, arcname=os.path.basename(fp))
#     buf.seek(0)
#     return buf


# def _mime_for(path):
#     mt, _ = mimetypes.guess_type(path)
#     return mt or "application/octet-stream"


# if st.button("Download", type="primary"):
#     if not url.strip():
#         st.error("Please paste an Instagram URL.")
#         st.stop()
#     if "instagram.com" not in url:
#         st.error("This doesn't look like an Instagram link.")
#         st.stop()
#     if not confirm:
#         st.warning("You must confirm permission to proceed.")
#         st.stop()

#     ydl_opts = {
#         "quiet": True,
#         "noprogress": True,
#         "restrictfilenames": True,
#     }

#     if keep_audio_only:
#         ydl_opts.update({
#             "format": "bestaudio[ext=mp3]/bestaudio",
#             "postprocessors": [
#                 {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
#             ],
#         })
#     else:
#         if format_note == "mp4":
#             ydl_opts.update({
#                 "format": "best[ext=mp4]/bestimage/best"
#             })
#         else:
#             ydl_opts.update({
#                 "format": "best/bestimage"
#             })

#     with tempfile.TemporaryDirectory() as tmpdir:
#         ydl_opts["outtmpl"] = os.path.join(tmpdir, "%(title).200B.%(id)s.%(ext)s")

#         # Save cookies.txt if uploaded
#         if cookies_file:
#             cookies_path = os.path.join(tmpdir, "cookies.txt")
#             with open(cookies_path, "wb") as f:
#                 f.write(cookies_file.getbuffer())
#             ydl_opts["cookiefile"] = cookies_path

#         status = st.status("Fetching media…", expanded=True)
#         try:
#             with YoutubeDL(ydl_opts) as ydl:
#                 info = ydl.extract_info(url, download=True)

#             status.update(label="Download complete.", state="complete")

#             files = glob.glob(os.path.join(tmpdir, "*"))
#             if not files:
#                 st.error("No files were produced. The link may be unsupported or private.")
#                 st.stop()

#             if len(files) == 1:
#                 fp = files[0]
#                 fname = os.path.basename(fp)
#                 with open(fp, "rb") as f:
#                     data = f.read()
#                 st.success("Ready! Click below to save.")
#                 st.download_button(
#                     label=f"⬇️ Download {fname}",
#                     data=data,
#                     file_name=fname,
#                     mime=_mime_for(fp),
#                 )
#             else:
#                 buf = _make_zip(files)
#                 st.success("Multiple files found (album/carousel). Download the ZIP.")
#                 st.download_button(
#                     label="⬇️ Download ZIP",
#                     data=buf,
#                     file_name="instagram_media.zip",
#                     mime="application/zip",
#                 )

#             # Show a tiny info panel
#             with st.expander("Details"):
#                 if isinstance(info, dict):
#                     title = info.get("title") or "—"
#                     uploader = info.get("uploader") or info.get("uploader_id") or "—"
#                     duration = info.get("duration")
#                     webpage_url = info.get("webpage_url") or url
#                     st.write({
#                         "title": title,
#                         "uploader": uploader,
#                         "duration_seconds": duration,
#                         "source": webpage_url,
#                     })

#         except Exception as e:
#             status.update(label="Failed.", state="error")
#             st.exception(e)
#             st.info(
#                 "If this is a private link, requires login, or Instagram blocked your request, "
#                 "try uploading your `cookies.txt` file (see instructions in the expander above)."
#             )




