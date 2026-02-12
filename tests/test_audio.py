import unittest
from unittest.mock import MagicMock, patch

from core.audio_manager import AudioManager


class TestAudioManager(unittest.TestCase):
    def setUp(self):
        # Reset singleton and initialized flag
        AudioManager._instance = None
        AudioManager._initialized = False

    @patch("core.audio_manager.pygame")
    def test_initialization(self, mock_pygame):
        manager = AudioManager()
        mock_pygame.mixer.init.assert_called_once()
        self.assertTrue(manager._initialized)

    @patch("core.audio_manager.pygame")
    @patch("core.audio_manager.os.path.exists")
    def test_play_existing_file(self, mock_exists, mock_pygame):
        mock_exists.return_value = True
        mock_sound = MagicMock()
        mock_pygame.mixer.Sound.return_value = mock_sound

        manager = AudioManager()
        manager.play("test.wav")

        mock_pygame.mixer.Sound.assert_called_with("test.wav")
        mock_sound.play.assert_called_once()
        self.assertIn("test.wav", manager.sounds)

    @patch("core.audio_manager.pygame")
    @patch("core.audio_manager.os.path.exists")
    def test_play_non_existent_file(self, mock_exists, mock_pygame):
        mock_exists.return_value = False
        manager = AudioManager()
        manager.play("missing.wav")

        mock_pygame.mixer.Sound.assert_not_called()

    @patch("core.audio_manager.pygame")
    @patch("core.audio_manager.os.path.exists")
    def test_play_error(self, mock_exists, mock_pygame):
        mock_exists.return_value = True
        mock_pygame.mixer.Sound.side_effect = Exception("Test Error")

        manager = AudioManager()
        # Should catch exception and log error, not crash
        manager.play("corrupt.wav")
