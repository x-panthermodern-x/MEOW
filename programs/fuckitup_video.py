from fractions import Fraction
from pathlib import Path
import json
import random
import shutil
import subprocess
import tempfile


def probe_video(ffprobe, video_path):
    result = subprocess.run([
        ffprobe,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=avg_frame_rate:format=duration",
        "-of", "json",
        str(video_path),
    ], check=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    if not streams:
        raise ValueError(f"No video stream found in: {video_path}")
    duration = float(data["format"]["duration"])
    frame_rate = float(Fraction(streams[0]["avg_frame_rate"]))
    if duration <= 0 or frame_rate <= 0:
        raise ValueError(f"Invalid duration or frame rate in: {video_path}")
    return duration, frame_rate


def randomized_output_path(input_file, requested_output, multiple_inputs):
    requested = Path(requested_output).expanduser()
    if not requested.suffix:
        requested = requested.with_suffix(".mp4")
    if multiple_inputs:
        requested = requested.with_name(
            f"{requested.stem}_{input_file.stem}{requested.suffix}"
        )
    return requested


def rearrange_video(input_directory, bpm, output_video):
    directory = Path(input_directory).expanduser()
    if not directory.is_dir():
        raise ValueError(f"Folder does not exist: {directory}")
    if bpm <= 0:
        raise ValueError("BPM must be greater than zero.")

    video_files = sorted(
        path for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() == ".mp4"
    )
    if not video_files:
        print(f"No MP4 files found in: {directory}")
        return []

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg is None or ffprobe is None:
        raise RuntimeError("FFmpeg and FFprobe must be installed and available on PATH.")

    beat_length = 60 / bpm
    outputs = []
    multiple_inputs = len(video_files) > 1

    for source in video_files:
        duration, frame_rate = probe_video(ffprobe, source)
        clip_length = min(beat_length, duration)
        start = random.uniform(0, max(0, duration - clip_length))
        destination = randomized_output_path(source, output_video, multiple_inputs)
        destination.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="meow_video_frames_") as temp_folder:
            temp_directory = Path(temp_folder)
            extracted = temp_directory / "extracted"
            shuffled = temp_directory / "shuffled"
            extracted.mkdir()
            shuffled.mkdir()

            subprocess.run([
                ffmpeg,
                "-hide_banner",
                "-loglevel", "error",
                "-ss", str(start),
                "-i", str(source),
                "-t", str(clip_length),
                "-vsync", "0",
                str(extracted / "%06d.png"),
            ], check=True)

            frames = sorted(extracted.glob("*.png"))
            if not frames:
                raise RuntimeError(f"No frames could be extracted from: {source}")
            random.shuffle(frames)
            for index, frame in enumerate(frames):
                shutil.copy2(frame, shuffled / f"{index:06d}.png")

            subprocess.run([
                ffmpeg,
                "-hide_banner",
                "-loglevel", "error",
                "-framerate", f"{frame_rate:.12g}",
                "-i", str(shuffled / "%06d.png"),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-y",
                str(destination),
            ], check=True)

        outputs.append(destination)
        print(f"Created: {destination.resolve()}")

    return outputs


def main():
    input_directory = input("Enter input directory: ").strip().strip('"')
    bpm = float(input("Enter BPM: "))
    output_video = input(
        "Enter output video path (including .mp4): "
    ).strip().strip('"')
    rearrange_video(input_directory, bpm, output_video)


if __name__ == "__main__":
    try:
        main()
    except (
        RuntimeError,
        ValueError,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
    ) as error:
        print(f"Error: {error}")
