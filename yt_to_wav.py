import youtube_dl
import os

url = input("Enter the YouTube URL: ")
output_path = input("Enter the output path: ")

# Ensure output path exists
if not os.path.exists(output_path):
    os.makedirs(output_path)

ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': output_path + '/%(title)s.%(ext)s',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'wav',
    }],
}

try:
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    print("Video converted and saved at", output_path)
except Exception as e:
    print("An error occurred:", e)
