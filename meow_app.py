from programs.FPS_BPM_Calc import fpsbpmlooper
from programs.meow_record_calc import run_record_calculator
from termcolor import colored
import subprocess
from pathlib import Path
import sys


APP_DIRECTORY = Path(__file__).resolve().parent


def run_program(script_name):
    """Run a program with the same Python interpreter used for MEOW."""
    module_name = f"programs.{Path(script_name).stem}"
    result = subprocess.run(
        [sys.executable, "-m", module_name],
        cwd=APP_DIRECTORY,
    )
    if result.returncode != 0:
        print(colored(
            f"\n{script_name} exited with error code {result.returncode}.",
            'red',
        ))


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
        print(colored("2.", 'cyan') + " YOUTUBE AUDIO - MP3 / WAV ")
        print(colored("3.", 'cyan') + " PNG to MP4 ")
        print(colored("4.", 'cyan') + " PNG to GIF ")
        print(colored("5.", 'cyan') + " MEOW RECORD CALCULATOR ")
        print(colored("6.", 'cyan') + " MIDI to CSV ")
        print(colored("7.", 'cyan') + " MIDI to OSC ")
        print(colored("8.", 'cyan') + " SHIFT AUDIO PITCH ")
        print(colored("9.", 'cyan') + " FUCK IT UP - AUDIO ")
        print(colored("10.", 'cyan') + " FUCK IT UP - VIDEO ")
        print(colored("11.", 'cyan') + " M4A to MP3 ")
        print(colored("X.", 'cyan') + " EXIT ")

        # Get the user's choice
        choice = input(colored("\nEnter number to RUN: ", 'red')).strip()

        try:
            # Run the selected script
            if choice == "1":
                input_fps = int(
                    input(colored("Enter the FPS value: ", 'red')))
                input_bpm = int(
                    input(colored("Enter the BPM value: ", 'red')))
                fpsbpmlooper(fps=input_fps, bpm=input_bpm)
            elif choice == "2":
                run_program('yt_to_mp3.py')
            elif choice == "3":
                from programs.ffmpeg_local import compile_video

                input_path = Path(
                    input(colored("PNG file or folder path: ", 'red')).strip().strip('"')
                ).expanduser()
                directory = input_path if input_path.is_dir() else input_path.parent
                compile_video(directory=directory)
            elif choice == "4":
                run_program('png_to_gif.py')
            elif choice == "5":
                run_record_calculator()
            elif choice == "6":
                run_program('midi_to_csv.py')
            elif choice == "7":
                run_program('midi_to_osc.py')
            elif choice == "8":
                run_program('shift_pitch.py')
            elif choice == "9":
                run_program('fuckitup.py')
            elif choice == "10":
                run_program('fuckitup_video.py')
            elif choice == "11":
                run_program('m4a2mp3.py')
            elif choice.lower() == "x":
                print(colored("\nGoodbye from MEOW.\n", 'red'))
                break
            else:
                print("Invalid choice.")
                continue
        except Exception as e:
            # if an error occurs, print the error message and start over
            print(e)
            continue


if __name__ == "__main__":
    main()
