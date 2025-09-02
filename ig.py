



import streamlit as st
import requests
import os
from yt_dlp import YoutubeDL

st.set_page_config(page_title="📥 Instagram Downloader", page_icon="📥", layout="centered")
st.title("📥 Instagram Downloader")

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
                "nocheckcertificate": True,
                "ignoreerrors": True,
                "geo_bypass": True,
            }
            if cookie_path:
                ydl_opts["cookiefile"] = cookie_path


            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if not info:
                    st.error("⚠️ Could not fetch media info. Try updating yt-dlp (`pip install -U yt-dlp`).")
                else:
                    title = info.get("title", "instagram_media")

                    # Case 1: Carousel / Album
                    if "entries" in info:
                        for i, entry in enumerate(info["entries"], start=1):
                            if entry is None:
                                continue  # skip broken entries

                            if "formats" in entry:  # video
                                video_url = entry["formats"][-1]["url"]
                                filename = f"{title}_{i}.mp4"
                                video_bytes = requests.get(video_url).content
                                st.video(video_url)
                                st.download_button(f"⬇️ Download Video {i}", video_bytes, filename, "video/mp4")

                            elif "url" in entry:  # image
                                image_url = entry["url"]
                                ext = entry.get("ext", "jpg")
                                filename = f"{title}_{i}.{ext}"
                                image_bytes = requests.get(image_url).content
                                st.image(image_url, caption=f"{title} ({i})")
                                st.download_button(f"⬇️ Download Image {i}", image_bytes, filename, f"image/{ext}")

                    # Case 2: Single video
                    elif "formats" in info:
                        video_url = info["formats"][-1]["url"]
                        filename = f"{title}.mp4"
                        video_bytes = requests.get(video_url).content
                        st.video(video_url)
                        st.download_button("⬇️ Download Video", video_bytes, filename, "video/mp4")

                    # Case 3: Single image
                    elif "url" in info:
                        image_url = info["url"]
                        ext = info.get("ext", "jpg")
                        filename = f"{title}.{ext}"
                        image_bytes = requests.get(image_url).content
                        st.image(image_url, caption=title)
                        st.download_button("⬇️ Download Image", image_bytes, filename, f"image/{ext}")

                    else:
                        st.error("⚠️ No downloadable media found. This post may require cookies.")
            # cleanup
            if cookie_path and os.path.exists(cookie_path):
                os.remove(cookie_path)

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
