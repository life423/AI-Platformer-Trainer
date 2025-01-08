import math
import random
import os
from typing import Optional, Tuple

import pygame
import torch
import logging

# If you have a logging setup function
from ai_platform_trainer.core.logging_config import setup_logging

# AI and model imports
from ai_platform_trainer.ai_model.model_definition.simple_model import SimpleModel
from ai_platform_trainer.ai_model.train_missile_model import SimpleMissileModel

# Data logger and entity imports
from ai_platform_trainer.core.data_logger import DataLogger
from ai_platform_trainer.entities.enemy_play import EnemyPlay
from ai_platform_trainer.entities.enemy_training import EnemyTrain
from ai_platform_trainer.entities.player_play import PlayerPlay
from ai_platform_trainer.entities.player_training import PlayerTraining

# Gameplay imports (config, collisions, menu, rendering, etc.)
from ai_platform_trainer.gameplay.config import config
from ai_platform_trainer.gameplay.menu import Menu
from ai_platform_trainer.gameplay.renderer import Renderer
from ai_platform_trainer.gameplay.collisions import handle_missile_collisions
from ai_platform_trainer.gameplay.spawner import (
    spawn_entities,
    respawn_enemy_with_fade_in,
)
from ai_platform_trainer.gameplay.utils import (
    compute_normalized_direction,
    find_valid_spawn_position,
)
from ai_platform_trainer.gameplay.modes.training_mode import TrainingMode

# Configuration manager imports for fullscreen settings
from config_manager import load_settings, save_settings


class Game:
    """Main class to run the Pixel Pursuit game."""

    def __init__(self) -> None:
        # If you have a custom logging setup, initialize it
        setup_logging()  # optional, depending on your config

        pygame.init()
        self.running: bool = True
        self.menu_active: bool = True
        self.mode: Optional[str] = None
        self.collision_count = 0

        # 1) Load user settings (fullscreen preference)
        settings = load_settings("settings.json")

        # 2) Initialize Pygame display
        if settings.get("fullscreen", False):
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(config.SCREEN_SIZE)

        # Optional: set window caption
        pygame.display.set_caption(config.WINDOW_TITLE)

        # 3) Store actual screen dimensions after set_mode
        self.screen_width: int = self.screen.get_width()
        self.screen_height: int = self.screen.get_height()

        self.clock = pygame.time.Clock()

        # 4) Create menu with actual screen size
        self.menu = Menu(self.screen_width, self.screen_height)
        self.renderer = Renderer(self.screen)

        # 5) Game entities / managers
        self.player: Optional[PlayerPlay] = None
        self.enemy: Optional[EnemyPlay] = None
        self.data_logger: Optional[DataLogger] = None
        self.missile_model: Optional[SimpleMissileModel] = None

        # Respawn logic
        self.respawn_delay = 1000
        self.respawn_timer = 0
        self.is_respawning = False

        logging.info("Game initialized.")

    def run(self) -> None:
        """Main game loop."""
        while self.running:
            current_time = pygame.time.get_ticks()
            self.handle_events()

            # If the menu is active, draw it. Otherwise update/play the game.
            if self.menu_active:
                self.menu.draw(self.screen)
            else:
                self.update(current_time)
                self.renderer.render(
                    self.menu, self.player, self.enemy, self.menu_active
                )

            pygame.display.flip()
            self.clock.tick(config.FRAME_RATE)

        # If we were training, save data before quitting
        if self.mode == "train" and self.data_logger:
            self.data_logger.save()

        pygame.quit()
        logging.info("Game loop exited and Pygame quit.")

    def start_game(self, mode: str) -> None:
        """
        Starts the game in the specified mode: "train" or "play".
        """
        self.mode = mode
        logging.info(f"Starting game in '{mode}' mode.")

        if mode == "train":
            # Training mode setup
            self.data_logger = DataLogger(config.DATA_PATH)
            self.player = PlayerTraining(self.screen_width, self.screen_height)
            self.enemy = EnemyTrain(self.screen_width, self.screen_height)
            self.train_missile = True

            spawn_entities(self)
            self.player.reset()

            self.training_mode_manager = TrainingMode(self)
        else:
            # Play mode setup
            self.player, self.enemy = self._init_play_mode()
            self.player.reset()
            spawn_entities(self)

            # Try to load the missile model
            missile_model_path = "models/missile_model.pth"
            if os.path.isfile(missile_model_path):
                logging.info(
                    f"Found missile model at '{missile_model_path}'. Loading..."
                )
                try:
                    self.missile_model = SimpleMissileModel()
                    self.missile_model.load_state_dict(
                        torch.load(missile_model_path, map_location="cpu")
                    )
                    self.missile_model.eval()
                except Exception as e:
                    logging.error(f"Failed to load missile model: {e}")
                    self.missile_model = None
            else:
                logging.warning(
                    f"No missile model found at '{missile_model_path}'. Skipping missile AI."
                )


    def handle_events(self) -> None:
        """Handle window and menu-related events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logging.info("Quit event detected. Exiting game.")
                self.running = False

            elif event.type == pygame.KEYDOWN:
                # If the menu is active, pass all keyboard events to the menu
                if self.menu_active:
                    selected_action = self.menu.handle_menu_events(event)
                    if selected_action:
                        self.check_menu_selection(selected_action)
                else:
                    # Not in menu: interpret ESC as exit, F as fullscreen, SPACE as shoot
                    if event.key == pygame.K_ESCAPE:
                        logging.info("Escape key pressed. Exiting game.")
                        self.running = False
                    elif event.key == pygame.K_f:
                        self.toggle_fullscreen()
                    elif event.key == pygame.K_SPACE and self.player:
                        self.player.shoot_missile()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Left-click
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if self.menu_active:
                    # Let the menu handle its own click detection
                    selected_action = self.menu.handle_menu_events(event)
                    if selected_action:
                        self.check_menu_selection(selected_action)
                else:
                    # In-game mouse logic here if desired
                    logging.debug(f"In-game left-click at ({mouse_x}, {mouse_y})")
                    # e.g. move player, spawn something, etc.

        # You could handle other mouse buttons or events (MOUSEMOTION, WHEEL, etc.) as needed

    def check_menu_selection(self, selected_action: str) -> None:
        """Handle actions selected from the menu."""
        if selected_action == "exit":
            logging.info("Exit action selected from menu.")
            self.running = False
        elif selected_action in ["train", "play"]:
            logging.info(f"'{selected_action}' selected from menu.")
            self.menu_active = False
            self.start_game(selected_action)

    def toggle_fullscreen(self) -> None:
        """
        Toggles fullscreen by flipping the 'fullscreen' setting in settings.json,
        reinitializing the display, and resizing the menu.
        """
        settings = load_settings("settings.json")
        current_state = settings.get("fullscreen", False)
        settings["fullscreen"] = not current_state

        # Re-init display
        if settings["fullscreen"]:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(config.SCREEN_SIZE)

        # Update screen dimensions
        self.screen_width = self.screen.get_width()
        self.screen_height = self.screen.get_height()

        # Recreate the menu to match new screen size
        self.menu = Menu(self.screen_width, self.screen_height)

        # Save updated preference
        save_settings(settings, "settings.json")
        logging.info(
            f"Fullscreen toggled to {settings['fullscreen']}. Display reset to {self.screen_width}x{self.screen_height}."
        )

    def _init_play_mode(self) -> Tuple[PlayerPlay, EnemyPlay]:
        """
        Initialize player and enemy for play mode, optionally load the enemy model.
        """
        model = SimpleModel(input_size=5, hidden_size=64, output_size=2)
        try:
            model.load_state_dict(torch.load(config.MODEL_PATH, map_location="cpu"))
            model.eval()
            logging.info("Enemy AI model loaded for play mode.")
        except Exception as e:
            logging.error(f"Failed to load enemy model: {e}")
            raise e

        player = PlayerPlay(self.screen_width, self.screen_height)
        enemy = EnemyPlay(self.screen_width, self.screen_height, model)
        logging.info("Initialized PlayerPlay and EnemyPlay for play mode.")
        return player, enemy

    def update(self, current_time: int) -> None:
        """Update game state each frame."""
        if self.mode == "train":
            self.training_mode_manager.update()
        elif self.mode == "play":
            self.play_update(current_time)
            self.check_missile_collisions()
            self.handle_respawn(current_time)

            # If enemy is fading in, keep updating it
            if self.enemy and self.enemy.fading_in:
                self.enemy.update_fade_in(current_time)

            # Update missiles if the player exists
            if self.player:
                self.player.update_missiles()

    def play_update(self, current_time: int) -> None:
        """Main update logic for play mode."""
        # Player input (movement, etc.)
        if self.player and not self.player.handle_input():
            logging.info("Player requested to quit.")
            self.running = False
            return

        # Enemy movement
        if self.enemy:
            try:
                self.enemy.update_movement(
                    self.player.position["x"],
                    self.player.position["y"],
                    self.player.step,
                    current_time,
                )
            except Exception as e:
                logging.error(f"Error updating enemy movement: {e}")
                self.running = False
                return

        # Check collision between player and enemy
        if self.check_collision():
            if self.enemy:
                self.enemy.hide()
            self.is_respawning = True
            self.respawn_timer = current_time + self.respawn_delay
            logging.info("Player-Enemy collision in play mode.")

        # If we have a missile AI model, apply it to any active missiles
        if self.missile_model and self.player and self.player.missiles:
            for missile in self.player.missiles:
                current_angle = math.atan2(missile.vy, missile.vx)

                px, py = self.player.position["x"], self.player.position["y"]
                ex, ey = self.enemy.pos["x"], self.enemy.pos["y"]
                dist_val = math.hypot(px - ex, py - ey)

                collision_val = 0.0
                input_state = torch.tensor(
                    [
                        [
                            px,  # player_x
                            py,  # player_y
                            ex,  # enemy_x
                            ey,  # enemy_y
                            missile.pos["x"],
                            missile.pos["y"],
                            current_angle,
                            dist_val,
                            collision_val,
                        ]
                    ],
                    dtype=torch.float32,
                )

                with torch.no_grad():
                    angle_delta = self.missile_model(input_state).item()

                new_angle = current_angle + angle_delta
                speed = 5.0
                missile.vx = math.cos(new_angle) * speed
                missile.vy = math.sin(new_angle) * speed

    def check_collision(self) -> bool:
        """
        Check if player and enemy collide.
        Returns True if a collision occurs, False otherwise.
        """
        if not self.player or not self.enemy:
            return False

        player_rect = pygame.Rect(
            self.player.position["x"],
            self.player.position["y"],
            self.player.size,
            self.player.size,
        )
        enemy_rect = pygame.Rect(
            self.enemy.pos["x"], self.enemy.pos["y"], self.enemy.size, self.enemy.size
        )
        collision = player_rect.colliderect(enemy_rect)

        if collision:
            logging.info("Collision detected between player and enemy.")
        return collision

    def check_missile_collisions(self) -> None:
        """
        Check if any missile collides with the enemy, triggering respawn if needed.
        """
        if not self.enemy or not self.player:
            return

        def respawn_callback():
            self.is_respawning = True
            self.respawn_timer = pygame.time.get_ticks() + self.respawn_delay
            logging.info("Missile-Enemy collision in play mode, enemy will respawn.")

        handle_missile_collisions(self.player, self.enemy, respawn_callback)

    def handle_respawn(self, current_time: int) -> None:
        """
        Handle enemy respawn after the delay if a collision has happened.
        """
        if (
            self.is_respawning
            and current_time >= self.respawn_timer
            and self.enemy
            and self.player
        ):
            respawn_enemy_with_fade_in(self, current_time)
