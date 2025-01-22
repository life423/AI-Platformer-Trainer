# file: ai_platform_trainer/entities/enemy.py

import torch
import math
import pygame
import logging
from typing import Optional


class Enemy:
    """
    Base enemy class. If a model is provided, the AI movement uses it;
    otherwise, subclasses might override 'update_movement' for pattern logic.
    """

    def __init__(
        self, screen_width: int, screen_height: int, model: Optional[torch.nn.Module]
    ):
        """
        Args:
            screen_width: Game screen width in pixels.
            screen_height: Game screen height in pixels.
            model: Optional PyTorch model for AI-based movement.
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.size = 50
        self.color = (173, 153, 228)
        self.pos = {"x": self.screen_width // 2, "y": self.screen_height // 2}
        self.model = model
        self.base_speed = max(2, screen_width // 400)
        self.visible = True

        # Fade-in attributes
        self.fading_in = False
        self.fade_start_time = 0
        self.alpha = 255

        # Create a surface for the enemy
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.image.fill((*self.color, self.alpha))

    def update_movement(
        self, player_x: float, player_y: float, player_speed: int, current_time: int = 0
    ):
        """
        Update enemy movement. Subclasses can override or call super().

        Args:
            player_x: Player's x-position.
            player_y: Player's y-position.
            player_speed: The player's current speed or step size.
            current_time: The current game time in ms. Default is 0 for backward compatibility.
        """
        if not self.visible:
            return

        if self.model is None:
            # If no AI model, do minimal or no movement here.
            return

        dist = math.hypot(player_x - self.pos["x"], player_y - self.pos["y"])
        state = torch.tensor(
            [[player_x, player_y, self.pos["x"], self.pos["y"], dist]],
            dtype=torch.float32,
        )

        with torch.no_grad():
            action = self.model(state)

        action_dx, action_dy = action[0].tolist()

        # Normalize
        length = math.hypot(action_dx, action_dy)
        if length > 0:
            action_dx /= length
            action_dy /= length
        else:
            action_dx, action_dy = 0.0, 0.0

        # Move at some fraction of player_speed
        speed = player_speed * 0.7
        self.pos["x"] += action_dx * speed
        self.pos["y"] += action_dy * speed

        # If you want time-based logic here, you can use `current_time`
        self._wrap_position()

    def _wrap_position(self):
        """Wrap around the screen if enemy goes off-screen."""
        if self.pos["x"] < -self.size:
            self.pos["x"] = self.screen_width
        elif self.pos["x"] > self.screen_width:
            self.pos["x"] = -self.size

        if self.pos["y"] < -self.size:
            self.pos["y"] = self.screen_height
        elif self.pos["y"] > self.screen_height:
            self.pos["y"] = -self.size

    def draw(self, screen: pygame.Surface):
        """Draw the enemy if visible."""
        if self.visible:
            self.image.set_alpha(self.alpha)
            screen.blit(self.image, (self.pos["x"], self.pos["y"]))

    def hide(self):
        """Hide the enemy entirely."""
        self.visible = False
        logging.info("Enemy hidden.")

    def show(self, current_time: int):
        """
        Show the enemy with a fade-in effect starting at current_time.
        Subclasses can override if they want a different approach.
        """
        self.visible = True
        self.fading_in = True
        self.fade_start_time = current_time
        self.alpha = 0
        self.image.set_alpha(self.alpha)
        logging.info("Enemy fade-in started.")

    def set_position(self, x: int, y: int):
        """Directly set the enemy's position."""
        self.pos["x"], self.pos["y"] = x, y

    def start_fade_in(self, current_time: int):
        """Initiate fade-in effect from 0 alpha to 255."""
        self.fading_in = True
        self.fade_start_time = current_time
        self.alpha = 0
        self.image.set_alpha(self.alpha)
        logging.info("Enemy fade-in started (base class).")

    def update_fade_in(self, current_time: int, fade_duration: int = 300):
        """Update fade-in effect if 'fading_in' is True."""
        if self.fading_in:
            elapsed = current_time - self.fade_start_time
            if elapsed >= fade_duration:
                self.alpha = 255
                self.fading_in = False
                logging.info("Enemy fade-in complete.")
            else:
                self.alpha = int((elapsed / fade_duration) * 255)
                logging.debug(f"Enemy fade-in alpha {self.alpha}.")
            self.image.set_alpha(self.alpha)
