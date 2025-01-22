# file: ai_platform_trainer/entities/player.py

import pygame
import random
import logging
from typing import List, Optional
from ai_platform_trainer.entities.missile import Missile


class Player:
    """
    A base Player class holding common attributes (position, size, color, step)
    and shared logic for missiles, drawing, and resetting.
    Subclasses (PlayerPlay, PlayerTraining) can override or extend specific methods.
    """

    def __init__(self, screen_width: int, screen_height: int, color=(0, 102, 204)):
        """
        Args:
            screen_width: The game screen's width in pixels.
            screen_height: The game screen's height in pixels.
            color: A default color for the player.
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.size = 50
        self.step = 5
        self.color = color
        # By default, center the player. Subclasses can override reset() if needed.
        self.position = {"x": self.screen_width // 2, "y": self.screen_height // 2}
        # Missiles list, so both 'play' and 'training' can store them here.
        self.missiles: List[Missile] = []

        logging.info("Base Player initialized with color=%s.", color)

    def reset(self) -> None:
        """
        Reset player to the screen's center by default,
        and clear any missiles. Subclasses can override for different logic.
        """
        self.position = {"x": self.screen_width // 2, "y": self.screen_height // 2}
        self.missiles.clear()
        logging.debug("Player reset to center with no missiles.")

    def handle_input(self) -> bool:
        """
        Base handle_input does nothing. PlayerPlay overrides this with actual keyboard logic.
        Return True if continuing, False if requesting to quit.
        """
        return True

    def shoot_missile(self) -> None:
        """
        Base shoot_missile: Subclasses can override if they use random angles or want multiple missiles, etc.
        Here, we do a simple single missile going horizontally to the right with random lifespan.
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
            logging.info("Base Player: Shot a missile going right.")
        else:
            logging.debug("Base Player: A missile is already active, ignoring shoot.")

    def update(self, enemy_x: float, enemy_y: float) -> None:
        """
        For 'training' or AI logic, base does nothing.
        Subclasses (PlayerTraining) can override to do advanced movement or AI patterns.
        """
        pass

    def update_missiles(self) -> None:
        """
        Let each missile move and remove expired/off-screen missiles.
        """
        current_time = pygame.time.get_ticks()
        for missile in self.missiles[:]:
            missile.update()
            # Check lifespan
            if current_time - missile.birth_time >= missile.lifespan:
                self.missiles.remove(missile)
                logging.debug("Missile removed after exceeding lifespan.")
                continue
            # Check screen bounds
            if (
                missile.pos["x"] < 0
                or missile.pos["x"] > self.screen_width
                or missile.pos["y"] < 0
                or missile.pos["y"] > self.screen_height
            ):
                self.missiles.remove(missile)
                logging.debug("Missile removed for leaving screen bounds.")

    def draw_missiles(self, screen: pygame.Surface) -> None:
        """Draw each missile onto the given surface."""
        for missile in self.missiles:
            missile.draw(screen)

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the player as a rectangle, plus any missiles."""
        pygame.draw.rect(
            screen,
            self.color,
            (self.position["x"], self.position["y"], self.size, self.size),
        )
        self.draw_missiles(screen)
