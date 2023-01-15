from FPS_BPM_Calc import fpsbpmlooper
from ffmpeg_local import compile_video
import os

def main():
    while True:
        print("")
        for i in range(2):
            print("////////////////")
        print("MEOW v0.1")
        for i in range(2):
            print("////////////////")
        print("")
        print("Available Programs:")
        print("")
        print("1. FPS and BPM Loop Calculator")
        print("2. PNG to MP4")

        print("")

        # Get the user's choice
        choice = input("Enter number to RUN: ")

        try:
            # Run the selected script
            if choice == "1":
                input_fps = int(input("Enter the FPS value: "))
                input_bpm = int(input("Enter the BPM value: "))
                fpsbpmlooper(fps=input_fps, bpm=input_bpm)
            elif choice == "2":
                input_path = input("Input Path: ")
                input_path = os.path.expanduser(input_path)
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
    
    