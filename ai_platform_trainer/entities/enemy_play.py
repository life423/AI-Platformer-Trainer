import torch
import math
import pygame
import logging
from typing import Optional, Tuple


class Enemy:
    def __init__(self, screen_width: int, screen_height: int, model):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.size = 50
        self.color = (173, 153, 228)
        self.pos = {"x": self.screen_width // 2, "y": self.screen_height // 2}
        self.model = model
        self.base_speed = max(2, screen_width // 400)
        self.visible = True  # Controls rendering

        # Fade-in attributes
        self.fading_in = False
        self.fade_alpha = 0
        self.fade_duration = 300  # milliseconds
        self.fade_start_time = 0

        # Create a Surface for the enemy with per-pixel alpha
        self.surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.surface.fill((*self.color, 255))  # Initial alpha set to 255

    def wrap_position(self, x: float, y: float) -> Tuple[float, float]:
        if x < -self.size:
            x = self.screen_width
        elif x > self.screen_width:
            x = -self.size
        if y < -self.size:
            y = self.screen_height
        elif y > self.screen_height:
            y = -self.size
        return x, y

    def update_movement(
        self, player_x: float, player_y: float, player_speed: int, current_time: int
    ):
        if not self.visible:
            return  # Do not update movement if enemy is not visible

        # State with 5 inputs: (player_x, player_y, self.pos["x"], self.pos["y"], dist)
        dist = math.sqrt(
            (player_x - self.pos["x"]) ** 2 + (player_y - self.pos["y"]) ** 2
        )
        state = torch.tensor(
            [[player_x, player_y, self.pos["x"], self.pos["y"], dist]],
            dtype=torch.float32,
        )

        with torch.no_grad():
            action = self.model(state)

        action_dx, action_dy = action[0].tolist()

        # Normalize action vector
        action_len = math.sqrt(action_dx**2 + action_dy**2)
        if action_len > 0:
            action_dx /= action_len
            action_dy /= action_len
        else:
            action_dx, action_dy = 0.0, 0.0  # Prevent division by zero

        speed = player_speed * 0.7
        self.pos["x"] += action_dx * speed
        self.pos["y"] += action_dy * speed

        # Wrap-around logic
        self.pos["x"], self.pos["y"] = self.wrap_position(self.pos["x"], self.pos["y"])

    def draw(self, screen: pygame.Surface) -> None:
        if self.visible:
            # Apply current alpha to the surface
            self.surface.set_alpha(self.fade_alpha)
            screen.blit(self.surface, (self.pos["x"], self.pos["y"]))

    def hide(self) -> None:
        """Hide the enemy by setting visibility to False."""
        self.visible = False
        logging.info("Enemy hidden due to collision.")

    def show(self, current_time: int) -> None:
        """
        Show the enemy and start fade-in.

        :param current_time: Current time in milliseconds
        """
        self.visible = True
        self.fading_in = True
        self.fade_alpha = 0
        self.fade_start_time = current_time
        logging.info("Enemy set to fade in.")

    def update_fade_in(self, current_time: int) -> None:
        """
        Update the fade-in effect based on elapsed time.

        :param current_time: Current time in milliseconds
        """
        if self.fading_in:
            elapsed = current_time - self.fade_start_time
            if elapsed >= self.fade_duration:
                self.fade_alpha = 255
                self.fading_in = False
                logging.info("Enemy fade-in completed.")
            else:
                # Calculate alpha based on elapsed time
                self.fade_alpha = int((elapsed / self.fade_duration) * 255)
                logging.debug(f"Enemy fade-in alpha: {self.fade_alpha}")

    def set_position(self, x: int, y: int) -> None:
        """Set the enemy's position."""
        self.pos["x"], self.pos["y"] = x, y
