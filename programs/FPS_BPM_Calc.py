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
        frames_for_loop = frames_per_beat * 4
        perfect_loop_frame = frames_for_loop - (frames_for_loop % frames_per_beat)
        perfect_loop_frame_int = int(perfect_loop_frame)
        print(colored("\nA one bar loop will occur on frame:",'light_red', attrs=['reverse']) + " " + colored(f" {perfect_loop_frame_int} || Exact: {perfect_loop_frame}", 'light_cyan'))

        # Identify the frame numbers for half and quarter notes
        half_note = frames_per_beat * 2
        quarter_note = frames_per_beat
        eighth_note = frames_per_beat / 2 

        # Print out the frames at which the half and quarter notes occur
        print("\nFrames at which the half note occurs: \n")
        for i in range(int(frames_for_loop)):
            if i % int(half_note) == 0:
                print(colored("{:>5} -- ".format(i), 'light_red'), end="")
        print("\n\n--------------------------------------------------\n")
        print("Frames at which the quarter note occurs: \n")
        for i in range(int(frames_for_loop)):
            if i % int(quarter_note) == 0:
                print(colored("{:>5} -- ".format(i), 'light_red'), end="")
        print("\n\n--------------------------------------------------\n")
        print("Frames at which the eighth note occurs: \n")
        for i in range(int(frames_for_loop)):
            if i % int(eighth_note) == 0:
                print(colored("{:>5} -- ".format(i), 'light_red'), end="")
        print("\n\n--------------------------------------------------\n")
        user_input = input("Enter 'x' to return to" + colored( " MEOW", 'light_red') + ": ")
        if user_input.lower() == "x":
            break
