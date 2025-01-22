# file: ai_platform_trainer/entities/player_play.py

import pygame
import logging
import random
from typing import List
from ai_platform_trainer.entities.player import Player
from ai_platform_trainer.entities.missile import Missile


class PlayerPlay(Player):
    """
    Player class for 'play' mode. Inherits from base Player and adds keyboard input logic.
    """

    def __init__(self, screen_width: int, screen_height: int):
        super().__init__(screen_width, screen_height, color=(0, 0, 139))
        # If you want a specific starting position for Play mode:
        self.position = {"x": screen_width // 4, "y": screen_height // 2}
        logging.info("PlayerPlay initialized at position=%s", self.position)

    def reset(self) -> None:
        """
        Override base reset to re-center at (screen_width//4, screen_height//2) if you want.
        Or call super().reset() if you just want the center.
        """
        self.position = {"x": self.screen_width // 4, "y": self.screen_height // 2}
        self.missiles.clear()
        logging.info(
            "PlayerPlay has been reset to the initial position (1/4 across screen)."
        )

    def handle_input(self) -> bool:
        """
        Check keyboard for WASD/arrow keys. Return True if continuing,
        or handle a special key for 'quit' if desired.
        """
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.position["x"] -= self.step
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.position["x"] += self.step
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.position["y"] -= self.step
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.position["y"] += self.step

        # Wrap-around logic
        if self.position["x"] < -self.size:
            self.position["x"] = self.screen_width
        elif self.position["x"] > self.screen_width:
            self.position["x"] = -self.size
        if self.position["y"] < -self.size:
            self.position["y"] = self.screen_height
        elif self.position["y"] > self.screen_height:
            self.position["y"] = -self.size

        return True

    def shoot_missile(self) -> None:
        """
        Example override to keep the random-lifespan logic from your original code.
        We also limit to one missile at a time, as in your previous approach.
        """
        if len(self.missiles) == 0:
            missile_start_x = self.position["x"] + self.size // 2
            missile_start_y = self.position["y"] + self.size // 2

            birth_time = pygame.time.get_ticks()
            random_lifespan = random.randint(500, 1500)

            missile = Missile(
                x=missile_start_x,
                y=missile_start_y,
                vx=5.0,
                vy=0.0,
                birth_time=birth_time,
                lifespan=random_lifespan,
            )
            self.missiles.append(missile)
            logging.info("Play mode: Shot a missile with random lifespan.")
        else:
            logging.debug("Attempted to shoot missile, but one is already active.")
