from fastapi import FastAPI, Body
from fastapi.responses import FileResponse
import yt_dlp
import os
import uuid
import logging
from zipfile import ZipFile
from starlette.background import BackgroundTask

app = FastAPI()

# # Cookie Setup
# try:
#     with open("/secrets/yt_cookies", "r") as file:
#         cookie_str = file.read()
# except FileNotFoundError:
#     print("The cookie file is missing! Using fallback dummy_cookies.txt...")
#     try:
#         with open("./secrets/yt_cookies.txt", "r") as file:
#             cookie_str = file.read()
#     except FileNotFoundError:
#         raise Exception("Neither /secrets/yt_cookies nor dummy_cookies.txt exists!")


# with open("cookies.txt", "w") as f:
#     f.write(cookie_str)


def download_audio_and_thumbnail(url: str, output_dir='downloads') -> tuple:
    os.makedirs(output_dir, exist_ok=True)
    unique_id = str(uuid.uuid4())
    audio_output_path = os.path.join(output_dir, f"{unique_id}.mp3")
    thumbnail_output_path = os.path.join(output_dir, f"{unique_id}.jpg")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, f'{unique_id}.%(ext)s'),
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }
        ],
        'writethumbnail': True,
        'quiet': True,
        "--cookies-from-browser": "chrome",
        # "cookiefile": "cookies.txt"
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Thumbnail is usually saved with a different extension (e.g., .webp or .jpg)
    # Find the thumbnail file and rename it to .jpg
    for ext in ['.jpg', '.webp', '.png']:
        temp_thumbnail = os.path.join(output_dir, f"{unique_id}{ext}")
        if os.path.exists(temp_thumbnail):
            os.rename(temp_thumbnail, thumbnail_output_path)
            break

    return audio_output_path, thumbnail_output_path

def cleanup_files(*file_paths):
    """Delete specified files if they exist."""
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logging.error(f"Failed to delete file {file_path}: {e}")

@app.post("/download")
def download(body: dict = Body(...)):
    url = body.get("url")
    if not url:
        return {"error": "URL is required"}

    audio_file, thumbnail_file = download_audio_and_thumbnail(url)
    
    # Create a zip file containing both audio and thumbnail
    zip_path = os.path.join('downloads', f"{os.path.basename(audio_file).split('.')[0]}.zip")
    with ZipFile(zip_path, 'w') as zipf:
        zipf.write(audio_file, os.path.basename(audio_file))
        if os.path.exists(thumbnail_file):
            zipf.write(thumbnail_file, os.path.basename(thumbnail_file))

    # Schedule cleanup after the response is sent
    cleanup_task = BackgroundTask(cleanup_files, audio_file, thumbnail_file, zip_path)

    return FileResponse(
        zip_path,
        media_type='application/zip',
        filename=os.path.basename(zip_path),
        background=cleanup_task
    )