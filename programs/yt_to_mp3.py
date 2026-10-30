from pathlib import Path
import shutil
import subprocess
import tempfile

import yt_dlp
from yt_dlp.utils import DownloadError

try:
    from termcolor import colored
except ImportError:
    def colored(text, *_args, **_kwargs):
        return text


def to_seconds(time_string):
    """Convert MM:SS or HH:MM:SS text to seconds."""
    parts = time_string.strip().split(":")
    if len(parts) not in (2, 3):
        raise ValueError("Use MM:SS or HH:MM:SS format.")

    try:
        values = [int(part) for part in parts]
    except ValueError as error:
        raise ValueError("Time values must be numbers.") from error

    if any(value < 0 for value in values) or values[-1] >= 60:
        raise ValueError("Seconds must be between 00 and 59.")
    if len(values) == 3 and values[-2] >= 60:
        raise ValueError("Minutes must be between 00 and 59 in HH:MM:SS.")

    if len(values) == 2:
        minutes, seconds = values
        return minutes * 60 + seconds

    hours, minutes, seconds = values
    return hours * 3600 + minutes * 60 + seconds


def choose_output_format():
    while True:
        choice = input(colored(
            "Output format - [1] MP3 or [2] WAV: ",
            "cyan",
        )).strip().lower()
        if choice in ("1", "mp3"):
            return "mp3"
        if choice in ("2", "wav"):
            return "wav"
        print("Please enter 1 for MP3 or 2 for WAV.")


def choose_cookie_browser():
    """Ask which browser contains the signed-in YouTube account."""
    browsers = {
        "1": "chrome",
        "2": "edge",
        "3": "firefox",
        "chrome": "chrome",
        "edge": "edge",
        "firefox": "firefox",
    }

    print(colored(
        "\nThis video requires a signed-in, age-verified YouTube account.",
        "yellow",
    ))
    print("Choose the browser where you are signed into YouTube:")
    print("  [1] Chrome")
    print("  [2] Edge")
    print("  [3] Firefox")
    print("  [4] Cancel")

    while True:
        choice = input(colored("Browser: ", "cyan")).strip().lower()
        if choice in browsers:
            return browsers[choice]
        if choice in ("4", "cancel", "q", "quit"):
            return None
        print("Please enter 1, 2, 3, or 4.")


def needs_browser_authentication(error):
    message = str(error).lower()
    indicators = (
        "age-restricted",
        "age restricted",
        "confirm your age",
        "sign in",
        "login required",
    )
    return any(indicator in message for indicator in indicators)


def run_download(url, options):
    """Run yt-dlp and allow its expected download errors to be handled cleanly."""
    with yt_dlp.YoutubeDL(options) as downloader:
        downloader.download([url])


def download_sample(url, output_directory, file_name, start, end, output_format):
    if end <= start:
        raise ValueError("The END time must be later than the START time.")

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError(
            "FFmpeg was not found. Install it and add its bin folder to PATH."
        )

    output_directory = Path(output_directory).expanduser()
    output_directory.mkdir(parents=True, exist_ok=True)
    destination = output_directory / f"{file_name}.{output_format}"

    with tempfile.TemporaryDirectory(prefix="meow_sampler_") as temp_folder:
        source_template = str(Path(temp_folder) / "source.%(ext)s")
        postprocessor = {
            "key": "FFmpegExtractAudio",
            "preferredcodec": output_format,
        }
        if output_format == "mp3":
            postprocessor["preferredquality"] = "320"

        options = {
            "format": "bestaudio/best",
            "outtmpl": source_template,
            "noplaylist": True,
            "postprocessors": [postprocessor],
        }

        try:
            run_download(url, options)
        except DownloadError as error:
            if not needs_browser_authentication(error):
                raise RuntimeError(f"YouTube download failed: {error}") from None

            browser = choose_cookie_browser()
            if browser is None:
                raise RuntimeError("Download cancelled.") from None

            print(colored(
                f"Retrying with the signed-in YouTube account from {browser.title()}...",
                "yellow",
            ))
            authenticated_options = {
                **options,
                "cookiesfrombrowser": (browser,),
            }
            try:
                run_download(url, authenticated_options)
            except DownloadError as authenticated_error:
                raise RuntimeError(
                    "YouTube authentication failed. Make sure you are signed into "
                    f"an age-verified YouTube account in {browser.title()}, close "
                    "that browser completely, and try again. "
                    f"Details: {authenticated_error}"
                ) from None

        source = Path(temp_folder) / f"source.{output_format}"
        if not source.exists():
            raise RuntimeError("The downloaded audio file could not be found.")

        command = [
            ffmpeg,
            "-hide_banner",
            "-loglevel", "error",
            "-ss", str(start),
            "-i", str(source),
            "-t", str(end - start),
            "-map_metadata", "0",
        ]
        if output_format == "mp3":
            command.extend(["-codec:a", "libmp3lame", "-b:a", "320k"])
        else:
            command.extend(["-codec:a", "pcm_s24le"])
        command.extend(["-y", str(destination)])

        result = subprocess.run(command)
        if result.returncode != 0:
            raise RuntimeError("FFmpeg could not create the requested sample.")

    print(colored(f"\nSAMPLE COMPLETE: {destination.resolve()}", "red"))


def main():
    print("\n////////////////")
    print("////////////////")
    print(colored("  MEOW SAMPLER  ", "red"))
    print("////////////////")
    print("////////////////\n")

    output_format = choose_output_format()
    start = to_seconds(input(colored(
        "Sample START time (MM:SS or HH:MM:SS): ",
        "cyan",
    )))
    end = to_seconds(input(colored(
        "Sample END time (MM:SS or HH:MM:SS): ",
        "cyan",
    )))
    url = input(colored("YouTube URL: ", "cyan")).strip()
    output_path = input(colored("Folder to save the file: ", "cyan")).strip()
    output_path = output_path.strip('"')
    file_name = input(colored("Name for the sample: ", "cyan")).strip()
    if not file_name:
        raise ValueError("The sample name cannot be empty.")

    download_sample(
        url,
        output_path,
        file_name,
        start,
        end,
        output_format,
    )


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, KeyboardInterrupt) as error:
        if isinstance(error, KeyboardInterrupt):
            print(colored("\nCancelled.", "red"))
        else:
            print(colored(f"Error: {error}", "red"))
