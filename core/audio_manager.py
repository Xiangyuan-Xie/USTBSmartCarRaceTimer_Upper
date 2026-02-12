import os

import pygame
from loguru import logger


class AudioManager:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AudioManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.init_mixer()
            self._initialized = True

    def init_mixer(self):
        try:
            pygame.mixer.init()
            self.sounds = {}
            logger.info("Audio mixer initialized successfully.")
        except Exception as e:
            logger.error(f"Audio mixer initialization failed: {e}")

    def play(self, file_path):
        if not os.path.exists(file_path):
            logger.warning(f"Audio file not found: {file_path}")
            return

        try:
            if file_path not in self.sounds:
                self.sounds[file_path] = pygame.mixer.Sound(file_path)

            self.sounds[file_path].play()
        except Exception as e:
            logger.error(f"Failed to play audio {file_path}: {e}")
