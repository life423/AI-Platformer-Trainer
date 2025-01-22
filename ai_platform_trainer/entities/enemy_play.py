# file: ai_platform_trainer/entities/enemy_play.py

import torch
import math
import pygame
import logging
from typing import Optional
from ai_platform_trainer.entities.enemy import Enemy


class EnemyPlay(Enemy):
    """
    EnemyPlay class for "play" mode enemies. Uses an AI model if provided.
    """

    def __init__(
        self, screen_width: int, screen_height: int, model: Optional[torch.nn.Module]
    ):
        super().__init__(screen_width, screen_height, model)
        self.size = 50
        self.color = (255, 215, 0)  # Gold
        self.pos = {"x": self.screen_width // 2, "y": self.screen_height // 2}
        self.base_speed = max(2, screen_width // 400)
        self.visible = True

        # Fade-in
        self.fading_in = False
        self.fade_alpha = 255
        self.fade_duration = 300
        self.fade_start_time = 0

        # Surface with alpha
        self.surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.surface.fill((*self.color, 255))

    def update_movement(
        self, player_x: float, player_y: float, player_speed: int, current_time: int = 0
    ):
        """
        If a model is provided, we do AI-based movement. Otherwise, we do minimal or none.
        """
        # Optionally call super for base AI logic
        # super().update_movement(player_x, player_y, player_speed, current_time)

        if not self.visible:
            return

        if self.model is None:
            # No AI, no movement
            return

        dist = math.hypot(player_x - self.pos["x"], player_y - self.pos["y"])
        state = torch.tensor(
            [[player_x, player_y, self.pos["x"], self.pos["y"], dist]],
            dtype=torch.float32,
        )

        with torch.no_grad():
            action = self.model(state)

        dx, dy = action[0].tolist()

        length = math.hypot(dx, dy)
        if length > 0:
            dx /= length
            dy /= length
        else:
            dx, dy = 0.0, 0.0

        speed = player_speed * 0.7
        self.pos["x"] += dx * speed
        self.pos["y"] += dy * speed

        self._wrap_position()

    def _wrap_position(self):
        if self.pos["x"] < -self.size:
            self.pos["x"] = self.screen_width
        elif self.pos["x"] > self.screen_width:
            self.pos["x"] = -self.size
        if self.pos["y"] < -self.size:
            self.pos["y"] = self.screen_height
        elif self.pos["y"] > self.screen_height:
            self.pos["y"] = -self.size

    def draw(self, screen: pygame.Surface):
        if self.visible:
            self.surface.set_alpha(self.fade_alpha)
            screen.blit(self.surface, (self.pos["x"], self.pos["y"]))

    def hide(self) -> None:
        self.visible = False
        logging.info("EnemyPlay hidden due to collision.")

    def show(self, current_time: int = 0) -> None:
        self.visible = True
        self.fading_in = True
        self.fade_alpha = 0
        self.fade_start_time = current_time
        logging.info("EnemyPlay set to fade in.")

    def update_fade_in(self, current_time: int):
        if self.fading_in:
            elapsed = current_time - self.fade_start_time
            if elapsed >= self.fade_duration:
                self.fade_alpha = 255
                self.fading_in = False
                logging.info("EnemyPlay fade-in completed.")
            else:
                self.fade_alpha = int((elapsed / self.fade_duration) * 255)
                logging.debug(f"EnemyPlay fade-in alpha: {self.fade_alpha}")
            self.surface.set_alpha(self.fade_alpha)
