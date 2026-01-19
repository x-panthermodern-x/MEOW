import os
import random
import subprocess

def parse_duration_seconds(duration_line):
    duration_value = duration_line.split("Duration:")[1].split(",")[0].strip()
    hours_str, minutes_str, seconds_str = duration_value.split(":")
    return int(hours_str) * 3600 + int(minutes_str) * 60 + float(seconds_str)

# Prompt user for input directory, BPM, and output video file
input_dir = input("Enter input directory: ")
while not os.path.isdir(input_dir):
    print("Invalid directory. Please enter a valid directory.")
    input_dir = input("Enter input directory: ")

bpm = int(input("Enter BPM: "))
while bpm <= 0:
    print("Invalid BPM. Please enter a positive number.")
    bpm = int(input("Enter BPM: "))

output_video = input("Enter output video file name (including the extension): ")

# Calculate length of one beat in seconds
beat_length = 60 / bpm
slice_length = beat_length / 4

# Get all video files in input directory
video_files = [f for f in os.listdir(input_dir) if f.endswith(".mp4")]
if len(video_files) == 0:
    print("No video files found in the directory.")
    exit()

# Loop through video files
for file in video_files:
    # Get the duration of the video
    output = subprocess.check_output(['ffmpeg', '-i', os.path.join(input_dir, file), '-vstats', '2>&1'])
    duration_line = [line for line in output.decode().split("\n") if "Duration" in line][0]
    duration = parse_duration_seconds(duration_line)
    # Randomly select a portion of the video to slice
    max_start = max(0, duration - (slice_length * 4))
    start = random.uniform(0, max_start)
    end = start + (slice_length * 4)
    # Use FFmpeg to extract the frames from the selected portion of the video
    output = subprocess.check_output(['ffmpeg', '-i', os.path.join(input_dir, file), '-ss', str(start), '-t', str((slice_length * 4)), '-vf', 'select=not(mod(n\,100))', '-vsync', 'vfr', 'frames/frame%03d.jpg'])
    # Get all the frames in the frames directory
    frames = [f for f in os.listdir("frames/") if f.endswith(".jpg")]
    random.shuffle(frames)
    # Use FFmpeg to create a new video from the randomly ordered frames
    output = subprocess.check_output(['ffmpeg', '-framerate', '24', '-i', 'frames/%03d.jpg', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', 'output_'+output_video])
    # Clean up the frames directory
    for frame in frames:
        os.remove("frames/"+frame)
    os.rmdir("frames/")
