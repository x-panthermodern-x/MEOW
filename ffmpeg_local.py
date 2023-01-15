import os
import subprocess

def compile_video(directory):
    # Get all the png files in the specified directory
    files = [f for f in os.listdir(directory) if f.endswith('.png')]
    # Sort the files by name
    files.sort()
    
    # Find the file names and the amount of digits appended to the end of the files
    file_names = []
    digits_count = 0
    for file in files:
        name, ext = os.path.splitext(file)
        file_name = name.split("_")[-1]
        file_names.append(file_name)
        digits_count = len(file_name)
        
    # rename the files
    for i, file in enumerate(files):
        os.rename(os.path.join(directory, file), os.path.join(directory, f'{file_names[i]}.png'))
    
    # Compile the video using FFmpeg
    subprocess.run(['ffmpeg', '-framerate', '24', '-i', f'{directory}/%0{digits_count}d.png', '-c:v', 'libx264', '-r', '24', '-pix_fmt', 'yuv420p', '-y', f'{directory}/output.mp4'])
    # Open the video in file explorer
    output_file = os.path.join(directory, 'output.mp4')
    output_file = os.path.abspath(output_file)
    subprocess.run(['explorer', output_file])
    output_file_parent_directory = os.path.dirname(output_file)
    subprocess.run(['explorer', output_file_parent_directory])

if __name__ == '__main__':
    directory = input("Enter the path of the directory containing the .png files: ")
    directory = os.path.expanduser(directory)
    compile_video(directory)

