from unittest.mock import patch
import unittest
from audiotown.main import ensure_ffmpeg

class TestDependencyChecks(unittest.TestCase):

    @patch("shutil.which")
    def test_ffmpeg_found(self, mock_which):
        mock_which.return_value = "/usr/local/bin/ffmpeg"
        result = ensure_ffmpeg()
        self.assertEqual(result, "/usr/local/bin/ffmpeg")
    
    @patch("shutil.which")
    @patch("click.confirm")
    def test_ffmpeg_missing_and_declined(self, mock_confirm, mock_which):
        """Test that the app exits if ffmpeg is missing and user says NO."""
        mock_which.return_value = None
        mock_confirm.return_value = False # User clicks 'n'
        
        # We expect the app to call sys.exit()
        with self.assertRaises(SystemExit):
            ensure_ffmpeg()

    @patch("shutil.which")
    @patch("click.confirm")
    def test_ffmpeg_missing_but_brew_exists(self, mock_confirm, mock_which):
        # side_effect returns these in order for each call
        # 1st call (ffmpeg) -> None
        # 2nd call (brew)    -> "/usr/local/bin/brew"
        mock_which.side_effect = [None, "/usr/local/bin/brew"]
        
        mock_confirm.return_value = False # User says 'No' to installing
        
        with self.assertRaises(SystemExit):
            ensure_ffmpeg()

if __name__ == "__main__":
    unittest.main()