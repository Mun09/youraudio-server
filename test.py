# test.py
import yt_dlp

def download_audio(url, output_path='downloads/%(title)s.%(ext)s'):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

if __name__ == "__main__":
    video_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'  # 원하는 URL 입력
    download_audio(video_url)
