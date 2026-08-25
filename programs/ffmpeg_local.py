from pathlib import Path
import os
import shutil
import subprocess
import tempfile


def compile_video(directory, frame_rate=24):
    directory = Path(directory).expanduser()
    if not directory.is_dir():
        raise ValueError(f"Folder does not exist: {directory}")

    files = sorted(
        path for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() == ".png"
    )
    if not files:
        raise ValueError(f"No PNG files found in: {directory}")
    if frame_rate <= 0:
        raise ValueError("Frame rate must be greater than zero.")

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError(
            "FFmpeg was not found. Install it and add its bin folder to PATH."
        )

    output_file = directory / "output.mp4"
    print(f"Compiling {len(files)} PNG files at {frame_rate} FPS...")

    # Copy frames into a temporary numbered sequence. Source images are never
    # renamed or modified.
    with tempfile.TemporaryDirectory(prefix="meow_png_frames_") as temp_folder:
        temp_directory = Path(temp_folder)
        for index, source in enumerate(files):
            shutil.copy2(source, temp_directory / f"{index:06d}.png")

        subprocess.run([
            ffmpeg,
            "-hide_banner",
            "-loglevel", "error",
            "-framerate", str(frame_rate),
            "-i", str(temp_directory / "%06d.png"),
            "-c:v", "libx264",
            "-r", str(frame_rate),
            "-pix_fmt", "yuv420p",
            "-y",
            str(output_file),
        ], check=True)

    print("      COMPLETED")
    print(f"File Location: {output_file.resolve()}")

    if os.name == "nt":
        subprocess.run(
            ["explorer", "/select,", str(output_file.resolve())],
            check=False,
        )

    return output_file
