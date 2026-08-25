from pathlib import Path
import json
import shutil
import subprocess


def atempo_filters(tempo_ratio):
    """Split a tempo ratio into FFmpeg-compatible 0.5-to-2.0 factors."""
    factors = []
    while tempo_ratio < 0.5:
        factors.append(0.5)
        tempo_ratio /= 0.5
    while tempo_ratio > 2.0:
        factors.append(2.0)
        tempo_ratio /= 2.0
    factors.append(tempo_ratio)
    return factors


def get_sample_rate(ffprobe, input_file):
    result = subprocess.run([
        ffprobe,
        "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=sample_rate",
        "-of", "json",
        str(input_file),
    ], check=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    if not streams:
        raise ValueError(f"No audio stream found in: {input_file}")
    return int(streams[0]["sample_rate"])


def change_pitch(input_directory, semitones):
    directory = Path(input_directory).expanduser()
    if not directory.is_dir():
        raise ValueError(f"Folder does not exist: {directory}")
    if not -48 <= semitones <= 48:
        raise ValueError("Pitch shift must be between -48 and +48 semitones.")

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg is None or ffprobe is None:
        raise RuntimeError("FFmpeg and FFprobe must be installed and available on PATH.")

    audio_files = sorted(
        path for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in (".mp3", ".wav")
    )
    if not audio_files:
        print(f"No MP3 or WAV files found in: {directory}")
        return []

    output_directory = directory / "pitched"
    output_directory.mkdir(exist_ok=True)
    pitch_ratio = 2 ** (semitones / 12)
    tempo_ratio = 1 / pitch_ratio
    outputs = []

    for source in audio_files:
        sample_rate = get_sample_rate(ffprobe, source)
        shifted_rate = max(1, round(sample_rate * pitch_ratio))
        filters = [
            f"asetrate={shifted_rate}",
            f"aresample={sample_rate}",
        ]
        filters.extend(
            f"atempo={factor:.12g}" for factor in atempo_filters(tempo_ratio)
        )

        destination = output_directory / source.name
        command = [
            ffmpeg,
            "-hide_banner",
            "-loglevel", "error",
            "-i", str(source),
            "-filter:a", ",".join(filters),
            "-map_metadata", "0",
        ]
        if destination.suffix.lower() == ".mp3":
            command.extend(["-codec:a", "libmp3lame", "-b:a", "320k"])
        else:
            command.extend(["-codec:a", "pcm_s24le"])
        command.extend(["-y", str(destination)])

        print(f"Pitch shifting: {source.name}")
        subprocess.run(command, check=True)
        outputs.append(destination)

    print(f"\nShifted {len(outputs)} file(s) by {semitones:+g} semitones.")
    print(f"Output folder: {output_directory.resolve()}")
    return outputs


def main():
    input_directory = input(
        "Enter the directory containing the audio files: "
    ).strip().strip('"')
    semitones = float(input(
        "Enter the semitones by which to shift the pitch (e.g. -5): "
    ))
    change_pitch(input_directory, semitones)


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
