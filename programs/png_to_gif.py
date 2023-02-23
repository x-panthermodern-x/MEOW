import os
import subprocess

# Prompt user for directory path
directory_path = input("Enter directory path: ")

# Check if the specified directory exists
if not os.path.exists(directory_path):
    print(f"Error: Directory '{directory_path}' does not exist.")
    exit()

# Call ffmpeg to generate GIF
command = f'ffmpeg -i {directory_path}/%05d.png -filter_complex "[0:v]crop=min(iw\,ih):min(iw\,ih),scale=128:128,split [a][b];[a] palettegen=reserve_transparent=on:transparency_color=0x00000000 [p];[b][p] paletteuse" -r 10 -y {directory_path}/output.gif'
try:
    subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    print(f"GIF saved to '{directory_path}/output.gif'.")
except subprocess.CalledProcessError as e:
    print(f"Error: {e.output.decode('utf-8')}")

