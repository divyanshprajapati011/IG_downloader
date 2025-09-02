

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
        if u.endswith(".mp4"):   # ✅ direct video link
            return u, "instagram_video.mp4", "url"
        else:  # ✅ non-video case use BytesIO
            r = requests.get(u)
            file_data = io.BytesIO(r.content)
            filename = "instagram_image.jpg"
            return file_data, filename, "bytes"
    else:
        # ✅ for multiple media → zip banani padegi
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for idx, u in enumerate(media_urls, 1):
                if u.endswith(".mp4"):
                    r = requests.get(u, stream=True)
                    zf.writestr(f"media_{idx}.mp4", r.content)
                else:
                    r = requests.get(u)
                    zf.writestr(f"media_{idx}.jpg", r.content)
        zip_buffer.seek(0)
        return zip_buffer, "instagram_media.zip", "bytes"


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
                    with cols[i % 3]:
                        if ".mp4" in u:
                            # 🎬 Custom video formatting (fixed size)
                            st.markdown(
                                f"""
                                <video controls style="width:100%; max-width:250px; border-radius:12px;">
                                    <source src="{u}" type="video/mp4">
                                </video>
                                """,
                                unsafe_allow_html=True
                            )
                        else:
                            r = requests.get(u)
                            file_bytes = io.BytesIO(r.content)
                            st.image(file_bytes, use_container_width=True)

                with st.spinner("Preparing download..."):
                    time.sleep(1)
                    data, fname, dtype = prepare_download(media_urls)

                if dtype == "url":
                    st.markdown(
                        f"[⬇️ Download Video]({data})",
                        unsafe_allow_html=True
                    )
                else:
                    st.download_button(
                        "⬇️ Download",
                        data=data,
                        file_name=fname,
                        mime="application/zip" if fname.endswith(".zip") else None,
                    )

            else:
                st.warning("⚠️ No media found!")

        except Exception as e:
            st.error(f"❌ Error: {e}")


