import csv
import mido

def convert_midi_to_csv(input_file):
    # Open the MIDI file
    mid = mido.MidiFile(input_file)

    # Get the output file name
    output_file = os.path.splitext(input_file)[0] + ".csv"

    # Open the output file for writing
    with open(output_file, "w", newline="") as f:
        # Create a CSV writer
        writer = csv.writer(f)

        # Write the header row
        writer.writerow(["track", "time", "type", "note", "velocity"])

        # Iterate through the MIDI file's tracks
        for track_index, track in enumerate(mid.tracks):
            # Iterate through the track's messages
            for msg in track:
                # Write the message to the CSV file
                if msg.type == 'note_on':
                    writer.writerow([track_index, msg.time, msg.type, msg.note, msg.velocity])
    print(f"Converted {input_file} to {output_file}")

if __name__ == "__main__":
    # Prompt the user for the path to the MIDI file
    input_file = input("Enter the path of the MIDI file: ")

    # Convert the MIDI file to a CSV file
    convert_midi_to_csv(input_file)
