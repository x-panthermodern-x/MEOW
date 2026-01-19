import os
import argparse
from pydub import AudioSegment

def change_pitch(input_directory, percentage):
    # Create new directory called "pitched" in the same location as input_directory
    output_directory = os.path.join(input_directory, "pitched")
    os.makedirs(output_directory, exist_ok=True)

    # Get all audio files in input_directory
    for filename in os.listdir(input_directory):
        if filename.endswith(".mp3") or filename.endswith(".wav"):
            input_filepath = os.path.join(input_directory, filename)
            # Open audio file using pydub
            audio = AudioSegment.from_file(input_filepath)
            # Change pitch by specified percentage
            audio_pitch_shifted = audio.effects.pitch_shift(n_semitones=percentage)
            # Save the modified file
            output_filepath = os.path.join(output_directory, filename)
            audio_pitch_shifted.export(output_filepath, format="mp3")

if __name__ == "__main__":
    input_directory = input("Enter the directory containing the audio files: ")
    percentage = float(input("Enter the semitones by which to shift the pitch (e.g. -5 for 5 semitones lower): "))
    change_pitch(input_directory, percentage)
