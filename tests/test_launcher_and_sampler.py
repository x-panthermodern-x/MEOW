import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import meow_app
from programs.FPS_BPM_Calc import fpsbpmlooper
from programs import yt_to_mp3


class LauncherTests(unittest.TestCase):
    def test_child_program_runs_as_module_from_app_directory(self):
        with patch("meow_app.subprocess.run") as run:
            run.return_value.returncode = 0
            meow_app.run_program("yt_to_mp3.py")

        self.assertEqual(
            run.call_args.args[0][1:],
            ["-m", "programs.yt_to_mp3"],
        )
        self.assertEqual(run.call_args.kwargs["cwd"], meow_app.APP_DIRECTORY)


class FpsCalculatorTests(unittest.TestCase):
    def test_invalid_values_are_rejected(self):
        with self.assertRaises(ValueError):
            fpsbpmlooper(0, 120)
        with self.assertRaises(ValueError):
            fpsbpmlooper(30, 0)


class YoutubeSamplerTests(unittest.TestCase):
    def test_time_parser(self):
        self.assertEqual(yt_to_mp3.to_seconds("01:30"), 90)
        self.assertEqual(yt_to_mp3.to_seconds("1:02:03"), 3723)
        with self.assertRaises(ValueError):
            yt_to_mp3.to_seconds("90")

    def test_mp3_and_wav_commands(self):
        class FakeDownloader:
            def __init__(self, options):
                self.options = options

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def download(self, _urls):
                output_format = self.options["postprocessors"][0]["preferredcodec"]
                source = Path(
                    self.options["outtmpl"].replace("%(ext)s", output_format)
                )
                source.touch()

        with tempfile.TemporaryDirectory() as output_directory:
            for output_format, codec in (
                ("mp3", "libmp3lame"),
                ("wav", "pcm_s24le"),
            ):
                with self.subTest(output_format=output_format):
                    with (
                        patch("programs.yt_to_mp3.yt_dlp.YoutubeDL", FakeDownloader),
                        patch("programs.yt_to_mp3.shutil.which", return_value="ffmpeg"),
                        patch("programs.yt_to_mp3.subprocess.run") as run,
                    ):
                        run.return_value.returncode = 0
                        yt_to_mp3.download_sample(
                            "https://example.test/video",
                            output_directory,
                            f"sample-{output_format}",
                            10,
                            20,
                            output_format,
                        )

                    command = run.call_args.args[0]
                    self.assertIn(codec, command)
                    self.assertNotIn("-ac", command)
                    self.assertTrue(command[-1].endswith(f".{output_format}"))


if __name__ == "__main__":
    unittest.main()
