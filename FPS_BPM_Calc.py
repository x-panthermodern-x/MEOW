import math
from termcolor import colored

def fpsbpmlooper(fps, bpm):
    while True:
        # # Prompt the user for the FPS value
        # fps = int(input("Enter the FPS value: "))

        # # Prompt the user for the BPM value
        # bpm = int(input("Enter the BPM value: "))

        # Calculate the number of frames for a perfect loop
        seconds_per_beat = 60 / bpm
        frames_per_beat = fps * seconds_per_beat
        frames_for_loop = math.ceil(frames_per_beat) * 4
        perfect_loop_frame = frames_for_loop - (frames_for_loop % frames_per_beat)
        print(colored(f"The perfect loop will occur on frame: {perfect_loop_frame}", 'red'))

        # Identify the frame numbers for half and quarter notes
        half_note = frames_per_beat / 2
        quarter_note = frames_per_beat / 4

        # Print out the frames at which the half and quarter notes occur
        print("Frames at which the half note occurs: ")
        for i in range(int(frames_for_loop)):
            if i % int(half_note) == 0:
                print(colored("{:>5} -- ".format(i), 'red'), end="")
        print()

        print("Frames at which the quarter note occurs: ")
        for i in range(int(frames_for_loop)):
            if i % int(quarter_note) == 0:
                print(colored("{:>5} -- ".format(i), 'red'), end="")
        print()
        user_input = input("Do you want to restart the script? (y/n)")
        if user_input.lower() == "n":
            break
