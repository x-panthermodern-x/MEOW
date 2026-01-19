import os
import random
from pydub import AudioSegment

# Prompt user for input directory, BPM, and output audio file
input_dir = input("Enter input directory: ")
while not os.path.isdir(input_dir):
    print("Invalid directory. Please enter a valid directory.")
    input_dir = input("Enter input directory: ")

bpm = int(input("Enter BPM: "))
while bpm <= 0:
    print("Invalid BPM. Please enter a positive number.")
    bpm = int(input("Enter BPM: "))

output_audio = input("Enter output audio file name (including the extension): ")

# Calculate length of one bar in milliseconds
beat_length = 60000 / bpm
one_bar_length = beat_length * 4
slice_length = int(one_bar_length / 4)

# Get all audio files in input directory
audio_files = [f for f in os.listdir(input_dir) if f.endswith(".mp3") or f.endswith(".wav")]
if len(audio_files) == 0:
    print("No audio files found in the directory.")
    exit()

# Loop through audio files
for file in audio_files:
    # Open audio file
    audio = AudioSegment.from_file(os.path.join(input_dir, file))
    # Get the duration of the audio
    duration = len(audio)
    # Randomly select a portion of the audio to slice
    max_start = max(0, duration - int(one_bar_length))
    start = random.randint(0, max_start)
    end = start + one_bar_length
    # Slice the audio
    sliced_audio = audio[start:end]
    # Reorder slices randomly
    slices = [sliced_audio[i:i+slice_length] for i in range(0, len(sliced_audio), slice_length)]
    random.shuffle(slices)
    # Concatenate slices back together in a loop
    loop = slices[0].empty()
    for s in slices:
        loop += s
    # Make sure the output audio is exactly one bar loop
    loop = loop.set_channels(1).set_frame_rate(44100)
    while len(loop) < one_bar_length:
        loop += AudioSegment.silent(duration=10)
    while len(loop) > one_bar_length:
        loop = loop[:len(loop) - 10]
    # Save loop to output file
    loop.export(output_audio, format="mp3")
