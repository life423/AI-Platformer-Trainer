import os
import pygame  # type: ignore
import json
import random

# Example import for the Enemy class in game.py
from entities.enemy import Enemy

# Import utility functions from core/utils.py
from core.utils import clamp_position



class Game:
    def __init__(self) -> None:
        """
        Initialize the game, including Pygame and game variables like player position.
        """
        self.mode = None  # Initialize mode to Non
        # Game configuration

        self.BACKGROUND_COLOR = (135, 206, 235)  # Light blue color
        self.PLAYER_COLOR = (0, 102, 204)  # A shade of blue for the player
        self.PLAYER_SIZE = 100  # Size of the player square
        self.PLAYER_STEP = 5  # Step size for player movement
        self.ENEMY_COLOR = (255, 69, 0)  # Orange-Red color for the enemy
        self.ENEMY_SIZE = 100  # Size of the enemy square

        # Initialize Pygame and set up player position
        self.screen = self.initialize_pygame()
        self.SCREEN_WIDTH = self.screen.get_width()
        self.SCREEN_HEIGHT = self.screen.get_height()

        # Enemy instance
        self.enemy = Enemy(
            start_x=100,
            start_y=300,
            screen_width=self.SCREEN_WIDTH,
            screen_height=self.SCREEN_HEIGHT,
        )

        self.player_pos = {"x": self.SCREEN_WIDTH // 2, "y": self.SCREEN_HEIGHT // 2}
        self.running = True

        # Menu state
        self.menu_active = True
        self.menu_options = ["Training", "Play", "Exit"]
        self.selected_option = 0  # Index of the currently selected menu option

        # List to store collision data for training
        self.collision_data = []

        # Frame counter for player movement
        self.player_movement_counter = 0
        self.player_current_direction = random.choice(
            [
                (self.PLAYER_STEP, 0),
                (-self.PLAYER_STEP, 0),
                (0, self.PLAYER_STEP),
                (0, -self.PLAYER_STEP),
            ]
        )

        # Set up data directory and file path
        self.data_dir, self.collision_data_file = self.setup_data_directory()

        # Load existing collision data if it matches the expected pattern
        if os.path.exists(self.collision_data_file):
            with open(self.collision_data_file, "r") as file:
                try:
                    data = json.load(file)
                    # Pattern check: Ensure every entry has valid 'player_position' and 'enemy_position'
                    is_valid = all(
                        isinstance(entry, dict)
                        and isinstance(entry.get("player_position"), dict)
                        and "x" in entry["player_position"]
                        and "y" in entry["player_position"]
                        and isinstance(entry.get("enemy_position"), dict)
                        and "x" in entry["enemy_position"]
                        and "y" in entry["enemy_position"]
                        and isinstance(entry.get("time"), (int, float))
                        and isinstance(entry.get("distance"), (int, float))
                        for entry in data
                    )
                    if is_valid:
                        self.collision_data = data
                except (json.JSONDecodeError, KeyError):
                    # If data is not valid, we reset it
                    self.collision_data = []

    def setup_data_directory(self) -> tuple[str, str]:
        """
        Set up the data directory and return paths for directory and collision data file.
        Returns:
            Tuple[str, str]: The data directory path and the collision data file path.
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(script_dir, "..", "data")
        os.makedirs(data_dir, exist_ok=True)
        collision_data_file = os.path.join(data_dir, "collision_data.json")
        return data_dir, collision_data_file

    def initialize_pygame(self) -> pygame.Surface:
        """
        Initialize all imported Pygame modules and set up the display in fullscreen mode.

        Returns:
            pygame.Surface: The screen surface to draw on.
        """
        pygame.init()
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        SCREEN_TITLE = "Pixel Pursuit"
        pygame.display.set_caption(SCREEN_TITLE)
        return screen

    def handle_events(self) -> None:
        """
        Listen for events such as quitting the game and player movement.
        Updates the running state and player's position accordingly.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN
                and event.key in [pygame.K_ESCAPE, pygame.K_q]
            ):
                self.running = False

            if self.menu_active:
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_UP, pygame.K_w]:
                        self.selected_option = (self.selected_option - 1) % len(
                            self.menu_options
                        )
                    elif event.key in [pygame.K_DOWN, pygame.K_s]:
                        self.selected_option = (self.selected_option + 1) % len(
                            self.menu_options
                        )
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        # Start the game with the selected mode
                        selected_option = self.menu_options[self.selected_option].lower()
                        if selected_option == "exit":
                            self.running = False
                        elif selected_option == "options":
                            # Implement options menu if needed
                            pass
                        else:
                            self.menu_active = False
                            self.start_game(mode=selected_option)
            else:
                # Game-specific events can be handled here
                pass

    def start_game(self, mode: str) -> None:
        """
        Set up the game for the selected mode.
        """
        self.mode = mode  # Ensure self.mode is set
        # Reset player and enemy positions if necessary
        self.player_pos = {"x": self.SCREEN_WIDTH // 2, "y": self.SCREEN_HEIGHT // 2}
        self.enemy.reset_position()
        # Reset collision data
        self.collision_data = []

    # Reset other game states as needed

    def handle_player_movement_random(self) -> None:
        """
        Update the player's position in a more varied, dynamic manner.
        """
        # Change direction every 20 frames
        if self.player_movement_counter % 20 == 0:
            self.player_current_direction = random.choice(
                [
                    (self.PLAYER_STEP, 0),
                    (-self.PLAYER_STEP, 0),
                    (0, self.PLAYER_STEP),
                    (0, -self.PLAYER_STEP),
                ]
            )

        # Apply the movement
        dx, dy = self.player_current_direction
        new_x = self.player_pos["x"] + dx
        new_y = self.player_pos["y"] + dy

        # Ensure the player does not move off-screen
        self.player_pos["x"] = clamp_position(
            new_x, 0, self.SCREEN_WIDTH - self.PLAYER_SIZE
        )
        self.player_pos["y"] = clamp_position(
            new_y, 0, self.SCREEN_HEIGHT - self.PLAYER_SIZE
        )

        # Increment movement counter
        self.player_movement_counter += 1

    def handle_player_movement_manual(self) -> None:
        """
        Continuously update the player's position based on pressed keys.
        The movement is restricted to ensure the player does not move off-screen.
        """
        keys = pygame.key.get_pressed()
        movement_directions = {
            pygame.K_LEFT: (-self.PLAYER_STEP, 0),
            pygame.K_a: (-self.PLAYER_STEP, 0),
            pygame.K_RIGHT: (self.PLAYER_STEP, 0),
            pygame.K_d: (self.PLAYER_STEP, 0),
            pygame.K_UP: (0, -self.PLAYER_STEP),
            pygame.K_w: (0, -self.PLAYER_STEP),
            pygame.K_DOWN: (0, self.PLAYER_STEP),
            pygame.K_s: (0, self.PLAYER_STEP),
        }

        for key, (dx, dy) in movement_directions.items():
            if keys[key]:
                new_x = self.player_pos["x"] + dx
                new_y = self.player_pos["y"] + dy
                # Ensure the player does not move off-screen
                self.player_pos["x"] = clamp_position(
                    new_x, 0, self.SCREEN_WIDTH - self.PLAYER_SIZE
                )
                self.player_pos["y"] = clamp_position(
                    new_y, 0, self.SCREEN_HEIGHT - self.PLAYER_SIZE
                )

    def log_game_state(self) -> None:
        """
        Log the current game state to be used for training.
        """
        self.collision_data.append(
            {
                "player_position": self.player_pos.copy(),
                "enemy_position": self.enemy.pos.copy(),
                "time": pygame.time.get_ticks(),
                "distance": (
                    (self.player_pos["x"] - self.enemy.pos["x"]) ** 2
                    + (self.player_pos["y"] - self.enemy.pos["y"]) ** 2
                )
                ** 0.5,
            }
        )

        # Save every 100 frames to avoid performance hit
        if len(self.collision_data) % 100 == 0:
            print("Saving collision data...")
            self.save_collision_data()

    def check_collision(self) -> bool:
        """
        Check for collision between the player and the enemy.

        Returns:
            bool: True if a collision is detected, otherwise False.
        """
        player_rect = pygame.Rect(
            self.player_pos["x"],
            self.player_pos["y"],
            self.PLAYER_SIZE,
            self.PLAYER_SIZE,
        )
        enemy_rect = pygame.Rect(
            self.enemy.pos["x"], self.enemy.pos["y"], self.enemy.size, self.enemy.size
        )
        return player_rect.colliderect(enemy_rect)

    def save_collision_data(self) -> None:
        """
        Save collision data to a JSON file.
        """
        with open(self.collision_data_file, "w") as file:
            json.dump(self.collision_data, file, indent=4)

    def run(self) -> None:
        """
        Main game loop that runs the game.
        Handles events, updates game state, and redraws the screen.
        """
        clock = pygame.time.Clock()

        while self.running:
            clock.tick(60)  # Cap the frame rate at 60 FPS
            self.handle_events()

            # Draw everything
            self.screen.fill(self.BACKGROUND_COLOR)
            if self.menu_active:
                self.draw_menu()
            else:
                # Handle player and enemy movement
                if self.mode == "training":
                    self.handle_player_movement_random()
                else:
                    self.handle_player_movement_manual()

                self.enemy.update_position(self.player_pos)

                # Log game state for training purposes
                self.log_game_state()

                # Check collision
                if self.check_collision():
                    print("Collision detected!")

                self.draw_gameplay()
            pygame.display.flip()

        # Save remaining collision data on game exit
        if self.collision_data:
            self.save_collision_data()

        pygame.quit()

    def draw_player(self) -> None:
        """
        Draw the player at the current position on the screen.
        The player is represented as a rectangle.
        """
        pygame.draw.rect(
            self.screen,
            self.PLAYER_COLOR,
            (
                self.player_pos["x"],
                self.player_pos["y"],
                self.PLAYER_SIZE,
                self.PLAYER_SIZE,
            ),
        )

    def draw_gameplay(self) -> None:
        """
        Draw all gameplay elements on the screen.
        """
        self.draw_player()
        self.enemy.draw(self.screen)

    # Colors
    def draw_menu(self) -> None:
        """
        Draw the menu on the screen.
        """
        # Colors
        background_color = self.BACKGROUND_COLOR  # Light blue
        title_color = (0, 51, 102)  # Dark blue for the title
        option_color = (245, 245, 245)  # Off-white for unselected options
        selected_color = (255, 215, 0)  # Gold for the selected option

        # Fonts
        title_font = pygame.font.Font(None, 100)
        option_font = pygame.font.Font(None, 60)  # Adjusted font size for better spacing

        # Render the title
        title_text = title_font.render("Pixel Pursuit", True, title_color)
        title_rect = title_text.get_rect(
            center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 5)
        )

        # Calculate spacing
        number_of_options = len(self.menu_options)
        spacing = 30  # Spacing between options

        # Start position for the first menu option
        options_start_y = title_rect.bottom + 50  # 50 pixels below the title

        # Render the menu options
        option_surfaces = []
        option_rects = []
        for index, option in enumerate(self.menu_options):
            if index == self.selected_option:
                color = selected_color
            else:
                color = option_color
            option_surface = option_font.render(option, True, color)
            option_rect = option_surface.get_rect(
                center=(
                    self.SCREEN_WIDTH // 2,
                    options_start_y + index * (option_font.get_height() + spacing),
                )
            )
            option_surfaces.append(option_surface)
            option_rects.append(option_rect)

        # Blit the title and options onto the screen
        self.screen.blit(title_text, title_rect)
        for surface, rect in zip(option_surfaces, option_rects):
            self.screen.blit(surface, rect)

    def reset_game(self) -> None:
        """
        Reset the game state to start a new game.
        """
        self.player_pos = {"x": self.SCREEN_WIDTH // 2, "y": self.SCREEN_HEIGHT // 2}
        self.enemy.reset_position()
        self.collision_data = []
        self.player_movement_counter = 0
