import os
import mido
from pythonosc import osc_bundle_builder
from pythonosc import osc_message_builder

def convert_midi_to_osc(input_file):
    # Open the MIDI file
    mid = mido.MidiFile(input_file)

    # Create the OSC bundle
    bundle = osc_bundle_builder.OscBundleBuilder(osc_bundle_builder.IMMEDIATELY)

    # Iterate through the MIDI file's tracks
    for track in mid.tracks:
        # Iterate through the track's messages
        for msg in track:
            if msg.type == 'note_on':
                # Extract the note and velocity from the message
                note = msg.note
                velocity = msg.velocity

                # Add a message to the bundle
                msg = osc_message_builder.OscMessageBuilder(address="/note")
                msg.add_arg(note)
                msg.add_arg(velocity)
                bundle.add_content(msg.build())

    # Get the output file name
    output_file = os.path.splitext(input_file)[0] + ".osc"

    # Save the bundle to a file
    with open(output_file, "wb") as f:
        f.write(bundle.build().dumps())
    print(f"Converted {input_file} to {output_file}")

if __name__ == "__main__":
    # Prompt the user for the MIDI file
    input_file = input("Enter the path of the MIDI file: ")

    # Convert the MIDI file to an OSC file
    convert_midi_to_osc(input_file)
