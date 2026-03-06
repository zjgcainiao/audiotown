from unittest.mock import patch
import unittest
from pathlib import Path
from click.testing import CliRunner
from audiotown.logger import logger

from audiotown.main import ensure_ffmpeg


class TestDependencyChecks(unittest.TestCase):

    @patch("audiotown.main.shutil.which")
    def test_ffmpeg_found(self, mock_which):
        mock_which.return_value = "/usr/local/bin/ffmpeg"
        result, _ = ensure_ffmpeg()
        self.assertEqual(result, "/usr/local/bin/ffmpeg")

    @patch("audiotown.main.shutil.which")
    @patch("click.confirm")
    def test_ffmpeg_missing_and_declined(self, mock_confirm, mock_which):
        """Test that the app exits if ffmpeg is missing and user says NO to install."""
        mock_which.return_value = None
        mock_confirm.return_value = False  # User clicks 'n'

        # We expect the app to call sys.exit()
        with self.assertRaises(SystemExit):
            ensure_ffmpeg()

    @patch("audiotown.main.shutil.which")
    @patch("audiotown.main.click.confirm")
    # args are in reverse decorator order
    def test_ffmpeg_missing_but_brew_exists(self, mock_confirm, mock_which):
        """test ffmpeg and ffprobe don't exist and there is no brew installed. yet user declines brew installation"""
        # side_effect returns these in order for each call
        # 1st call (ffmpeg) -> None
        # 2nd call (brew)    -> "/usr/local/bin/brew"
        mock_which.side_effect = [None, None, "/usr/local/bin/brew"]

        mock_confirm.return_value = False  # User says 'No' to installing

        with self.assertRaises(SystemExit):
            ensure_ffmpeg()


# Scenario 1: --help works
# args are in reverse decorator order:
from audiotown.main import cli_runner


class TestCLI(unittest.TestCase):
    def test_cli_help_option(self):

        # logger.stream(f"---- run {self.__name__}\n")
        runner = CliRunner()
        result = runner.invoke(cli_runner, ["--help"])
        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn("stats", result.output)
        # logger.stream(f"----- end of  {self.__str__}\n")
        # logger.stream(f"------------------\n")

    def test_cli_version_option_success(self):
        runner = CliRunner()
        result = runner.invoke(cli_runner, ["--version"])
        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn("version", result.output)

    def test_cli_stats_no_folder_fails(self):
        runner = CliRunner()
        result = runner.invoke(cli_runner, ["stats"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Missing argument", result.output)


    def test_stats_default_report_path_is_cwd(self):
        runner = CliRunner()

        with runner.isolated_filesystem():
            scan_folder = Path("music")
            scan_folder.mkdir()

            result = runner.invoke(
                cli_runner, ["stats", str(scan_folder), "--report-path"]
            )
            self.assertEqual(result.exit_code, 0, msg=result.output)

            # If your default output is ./audiotown_export
            export_dir = Path("audiotown_stats")
            with self.subTest("default report_path should be CWD"):
            #     self.assertTrue(Path("audiotown_stats").exists(),f"{Path("audiotown_stats").exists()}")
                self.assertTrue(export_dir.exists(), f"Expected export dir in sandbox CWD")
    
    def test_stats_explicit_report_path(self):
        runner = CliRunner()

        with runner.isolated_filesystem():
            scan_folder = Path("music")
            scan_folder.mkdir()

            report_root = Path(f"reports")
            report_root.mkdir()

            result = runner.invoke(
                cli_runner,
                ["stats", str(scan_folder), f"--report-path={report_root}"]
            )
            self.assertEqual(result.exit_code, 0, msg=result.output)
            print("OUTPUT:\n", result.output)
            export_dir = report_root / "audiotown_stats"
            self.assertTrue(export_dir.exists(), f"Expected export dir created")

    @patch("audiotown.main.Path.exists")
    def test_stats_nonexistent_folder_fails(self, mock_exists):
        mock_exists.return_value = False
        runner = CliRunner()
        result = runner.invoke(cli_runner, ["stats", "/fake/path"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertEqual(result.exit_code, 2)


if __name__ == "__main__":
    unittest.main()
