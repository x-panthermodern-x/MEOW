from pathlib import Path
import shutil
import subprocess


def convert_m4a_to_mp3(folder_path):
    """Convert every M4A file in a folder to a 320 kbps MP3."""
    folder = Path(folder_path).expanduser()
    if not folder.is_dir():
        raise ValueError(f"Folder does not exist: {folder}")

    m4a_files = sorted(
        path for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() == ".m4a"
    )
    if not m4a_files:
        print(f"No M4A files found in: {folder}")
        return

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError(
            "FFmpeg was not found. Install it and add its bin folder to PATH."
        )

    converted = 0
    for source in m4a_files:
        destination = source.with_suffix(".mp3")
        print(f"Converting: {source.name} -> {destination.name}")

        # No -ac option is used, so FFmpeg retains the source channel count.
        result = subprocess.run([
            ffmpeg,
            "-hide_banner",
            "-loglevel", "error",
            "-i", str(source),
            "-map_metadata", "0",
            "-codec:a", "libmp3lame",
            "-b:a", "320k",
            "-y",
            str(destination),
        ])

        if result.returncode == 0:
            converted += 1
        else:
            print(f"Could not convert: {source.name}")

    print(f"\nConverted {converted} of {len(m4a_files)} file(s).")
    print(f"Output folder: {folder.resolve()}")


def main():
    folder_path = input("Enter the folder containing M4A files: ").strip()
    folder_path = folder_path.strip('"')
    convert_m4a_to_mp3(folder_path)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as error:
        print(f"Error: {error}")
