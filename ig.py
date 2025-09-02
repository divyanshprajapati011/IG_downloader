import streamlit as st
import instaloader
import requests, io, zipfile, time

st.set_page_config(page_title="📥 Instagram Downloader", layout="centered")
st.title("📥 Instagram Downloader ")

url = st.text_input("🔗 Enter Instagram Post/Reel URL:")

L = instaloader.Instaloader(
    download_videos=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False
)

def get_media_links(url):
    """Extract media URLs with Instaloader"""
    shortcode = url.split("/")[-2]
    post = instaloader.Post.from_shortcode(L.context, shortcode)
    media_urls = []
    if post.typename == "GraphImage":
        media_urls.append(post.url)
    elif post.typename == "GraphVideo":
        media_urls.append(post.video_url)
    elif post.typename == "GraphSidecar":  # Carousel
        for node in post.get_sidecar_nodes():
            media_urls.append(node.video_url if node.is_video else node.display_url)
    return media_urls

def prepare_download(media_urls):
    """Return file or zip"""
    if len(media_urls) == 1:
        u = media_urls[0]
        r = requests.get(u)
        file_data = io.BytesIO(r.content)
        filename = "instagram_video.mp4" if ".mp4" in u else "instagram_image.jpg"
        return file_data, filename
    else:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for idx, u in enumerate(media_urls, 1):
                r = requests.get(u)
                ext = ".mp4" if ".mp4" in u else ".jpg"
                zf.writestr(f"media_{idx}{ext}", r.content)
        zip_buffer.seek(0)
        return zip_buffer, "instagram_media.zip"


# ================= Preview + Download ==================
if url:
    if st.button("🔍 Preview Media"):
        try:
            st.subheader("🔍 Preview")
            with st.spinner("⏳ Fetching media, please wait..."):
                media_urls = get_media_links(url)

            if media_urls:
                st.success("✅ Preview ready!")

                # ✅ Grid layout (3 columns per row)
                cols = st.columns(3)
                for i, u in enumerate(media_urls):
                    r = requests.get(u)
                    file_bytes = io.BytesIO(r.content)

                    with cols[i % 3]:  # round-robin placement
                        if ".mp4" in u:
                            st.video(file_bytes)
                        else:
                            st.image(file_bytes, use_container_width=True)

                with st.spinner("Preparing download..."):
                    time.sleep(1)
                    data, fname = prepare_download(media_urls)

                st.download_button(
                    "⬇️ Download All",
                    data=data,
                    file_name=fname,
                    mime="application/zip" if fname.endswith(".zip") else None,
                )

            else:
                st.warning("⚠️ No media found!")

        except Exception as e:
            st.error(f"❌ Error: {e}")
