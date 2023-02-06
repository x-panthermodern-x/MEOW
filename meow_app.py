from FPS_BPM_Calc import fpsbpmlooper
from ffmpeg_local import compile_video
from termcolor import colored
import subprocess
import os
import termcolor

COLORS = termcolor


def main():
    while True:
        print("")
        for i in range(2):
            print("////////////////")
        print(colored("   MEOW v0.1   ", 'red', ))
        for i in range(2):
            print("////////////////")

        print(colored("\n Available Programs:\n",
              'red', attrs=['reverse',]))
        print(colored("1.", 'cyan') + " MEOW FPS / BPM ")
        print(colored("2.", 'cyan') + " MEOW SAMPLER ")
        print(colored("3.", 'cyan') + " PNG to MP4 ")

        # Get the user's choice
        choice = input(colored("\nEnter number to RUN: ", 'red'))

        try:
            # Run the selected script
            if choice == "1":
                input_fps = int(
                    input(colored("Enter the FPS value: ", 'red')))
                input_bpm = int(
                    input(colored("Enter the BPM value: ", 'red')))
                fpsbpmlooper(fps=input_fps, bpm=input_bpm)
            elif choice == "2":
                subprocess.run(['python', 'yt_to_mp3.py'])
            elif choice == "3":
                input_path = input((colored("Input Path: ", 'red')))
                input_path = os.path.dirname(input_path)
                compile_video(directory=input_path)
            else:
                print("Invalid choice.")
                continue
        except Exception as e:
            # if an error occurs, print the error message and start over
            print(e)
            continue


if __name__ == "__main__":
    main()
