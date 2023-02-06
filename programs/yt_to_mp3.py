import youtube_dl
import os
import subprocess
from termcolor import colored

print("")
for i in range(2):
    print("////////////////")
print(colored("  MEOW SAMPLER  ", 'red', ))
for i in range(2):
    print("////////////////")

def to_seconds(time_str):
    minutes, seconds = map(int, time_str.split(':'))
    return minutes * 60 + seconds

start_str = input((colored("Sample START time in mm:ss format: ", 'cyan')))
start = to_seconds(start_str)
print("")
end_str = input((colored("Sample END time in mm:ss format: ", 'cyan')))
end = to_seconds(end_str)
print("")
input_path = input((colored("Enter the URL for the YouTube video: " , 'cyan')))
print("")
output_path = input((colored("Enter the path to save the MP3 file: " , 'cyan')))
print("")
file_name = input((colored("Create a name for the sample: " , 'cyan')))
print("")

ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320',
    }],
    'outtmpl': os.path.join(output_path, file_name + '.%(ext)s'),
    'playliststart': start,
    'playlistend': end,
}

with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    ydl.download([input_path])

output_file = os.path.join(output_path, file_name + '.mp3')

start_time = f"{start // 60}:{start % 60}"
duration = f"{(end - start) // 60}:{(end - start) % 60}"

new_file = os.path.join(output_path, file_name + '_cropped.mp3')
if os.path.exists(new_file):
    os.remove(new_file)

ffmpeg_command = f"ffmpeg -nostats -loglevel 0 -ss {start_time} -t {duration} -i {output_file} -acodec copy {new_file} "

subprocess.run(ffmpeg_command, shell=True)

os.remove(os.path.join(output_path, file_name + '.mp3'))
os.rename(os.path.join(output_path, file_name + '_cropped.mp3'), os.path.join(output_path, file_name + '.mp3'))

print((colored("SAMPLE COMPLETE and OUTPUT to: " + f"{output_path}", 'red')))
