import streamlit as st
import requests
import os
from yt_dlp import YoutubeDL



st.set_page_config(page_title="📥 Instagram Downloader", page_icon="📥", layout="centered")
st.title("📥 Instagram Downloader")




# ✅ Guide section for cookies
with st.expander("📑 How to get cookies.txt (for private/login-required posts)", expanded=False):
    st.markdown(
        """
        To download *private posts* or if Instagram blocks downloads, you need to provide your cookies.txt.

        ### Step-by-step:
        1. Open Instagram in your browser and *log in* to your account.
        2. Install this extension:
           - [Get cookies.txt (Chrome)](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
           - [Get cookies.txt (Firefox)](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
        3. Once logged in, click the extension icon → click *Export*.
        4. Save the file as cookies.txt on your computer.
        5. Upload it below in the uploader box.
        6. Now the downloader will work for private posts / login required content.

        ⚠️ Note: Cookies expire after some time. If download stops working, repeat the steps to get a fresh cookies.txt.
        """
    )

url = st.text_input("Paste Instagram Reel/Post URL:")

cookies_file = st.file_uploader("Upload cookies.txt (only if needed for private posts)", type=["txt"])

if st.button("Download"):
    if not url:
        st.error("❌ Please paste a valid Instagram link")
    else:
        try:
            # Save cookies file temporarily if uploaded
            cookie_path = None
            if cookies_file is not None:
                cookie_path = os.path.join("cookies.txt")
                with open(cookie_path, "wb") as f:
                    f.write(cookies_file.read())

            # yt-dlp options
            ydl_opts = {
                "outtmpl": "%(title)s.%(ext)s",
                "format": "best",
                "quiet": True,
            }
            if cookie_path:
                ydl_opts["cookiefile"] = cookie_path

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)  # just extract
                download_url = info.get("url")

                if not download_url:
                    st.error("⚠️ No downloadable video found (maybe this is an image post).")
                else:
                    filename = info.get("title", "instagram_video") + ".mp4"
                    video_bytes = requests.get(download_url).content

                    st.video(download_url)
                    st.download_button(
                        label="⬇️ Download Video",
                        data=video_bytes,
                        file_name=filename,
                        mime="video/mp4",
                    )

            # cleanup
            if cookie_path and os.path.exists(cookie_path):
                os.remove(cookie_path)

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
