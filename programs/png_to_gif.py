from pathlib import Path
import shutil
import subprocess


def png_to_gif(directory_path, frame_rate=10, size=128):
    directory = Path(directory_path).expanduser()
    if not directory.is_dir():
        raise ValueError(f"Folder does not exist: {directory}")
    if frame_rate <= 0 or size <= 0:
        raise ValueError("Frame rate and output size must be greater than zero.")

    files = sorted(
        path for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() == ".png"
    )
    if not files:
        raise ValueError(f"No PNG files found in: {directory}")

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError(
            "FFmpeg was not found. Install it and add its bin folder to PATH."
        )

    # ffconcat accepts arbitrary PNG filenames and avoids renaming source files.
    concat_file = directory / ".meow-gif-frames.txt"
    output_file = directory / "output.gif"
    frame_duration = 1 / frame_rate
    concat_lines = []
    for image in files:
        escaped_path = str(image.resolve()).replace("'", "'\\''")
        concat_lines.append(f"file '{escaped_path}'")
        concat_lines.append(f"duration {frame_duration:.9f}")
    escaped_last = str(files[-1].resolve()).replace("'", "'\\''")
    concat_lines.append(f"file '{escaped_last}'")
    concat_file.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")

    video_filter = (
        f"crop='min(iw,ih)':'min(iw,ih)',scale={size}:{size}:flags=lanczos,"
        "split[a][b];[a]palettegen=reserve_transparent=on[p];[b][p]paletteuse"
    )
    try:
        subprocess.run([
            ffmpeg,
            "-hide_banner",
            "-loglevel", "error",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-filter_complex", video_filter,
            "-loop", "0",
            "-y",
            str(output_file),
        ], check=True)
    finally:
        concat_file.unlink(missing_ok=True)

    print(f"GIF saved to: {output_file.resolve()}")
    return output_file


def main():
    directory_path = input("Enter directory path: ").strip().strip('"')
    png_to_gif(directory_path)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}")
