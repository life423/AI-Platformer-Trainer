# file: ai_platform_trainer/entities/enemy_training.py

import random
import math
import logging
from ai_platform_trainer.entities.enemy import Enemy
from ai_platform_trainer.utils.helpers import wrap_position


class EnemyTraining(Enemy):
    """
    EnemyTrain is a subclass of Enemy that uses pattern-based movement
    to generate training data or mimic certain AI behaviors.
    """

    DEFAULT_SIZE = 50
    DEFAULT_COLOR = (173, 153, 228)
    PATTERNS = ["random_walk", "circle_move", "diagonal_move", "pursue"]
    WALL_MARGIN = 20
    PURSUIT_SPEED_FACTOR = 0.8

    def __init__(self, screen_width: int, screen_height: int):
        super().__init__(screen_width, screen_height, model=None)
        self.size = self.DEFAULT_SIZE
        self.color = self.DEFAULT_COLOR
        self.pos = {
            "x": self.screen_width // 2,
            "y": self.screen_height // 2,
        }
        self.base_speed = max(2, screen_width // 400)
        self.visible = True

        # Timers and states controlling pattern selection
        self.state_timer = 0
        self.current_pattern = None

        # Forced escape logic
        self.forced_escape_timer = 0
        self.forced_angle = None
        self.forced_speed = None

        # Circle-move parameters
        self.circle_center = (self.pos["x"], self.pos["y"])
        self.circle_angle = 0.0
        self.circle_radius = 100

        # Diagonal-move parameters
        self.diagonal_direction = (1, 1)

        # Random-walk parameters
        self.random_walk_timer = 0
        self.random_walk_angle = 0.0
        self.random_walk_speed = self.base_speed

        # Initialize pattern
        self.switch_pattern()

    def update_movement(self, player_x, player_y, player_speed, current_time=0):
        """
        Overrides base to handle pattern-based movement.
        Calls super() if we want base AI logic, or just do pattern logic here.
        """
        if self.forced_escape_timer > 0:
            self.forced_escape_timer -= 1
            self.apply_forced_escape_movement()
        else:
            self.state_timer -= 1
            if self.state_timer <= 0:
                self.switch_pattern()

            if self.current_pattern == "random_walk":
                self.random_walk_pattern()
            elif self.current_pattern == "circle_move":
                self.circle_pattern()
            elif self.current_pattern == "diagonal_move":
                self.diagonal_pattern()
            elif self.current_pattern == "pursue":
                self.pursue_pattern(player_x, player_y, player_speed)

        # Wrap around
        self.pos["x"], self.pos["y"] = wrap_position(
            self.pos["x"],
            self.pos["y"],
            self.screen_width,
            self.screen_height,
            self.size,
        )

        # (Optional) If you want the base AI logic:
        # super().update_movement(player_x, player_y, player_speed, current_time)

        # If you want to do time-based logic:
        # e.g. if current_time > 5000: do something special

    def switch_pattern(self):
        if self.forced_escape_timer > 0:
            return

        new_pattern = self.current_pattern
        while new_pattern == self.current_pattern:
            new_pattern = random.choice(self.PATTERNS)
        self.current_pattern = new_pattern
        self.state_timer = random.randint(120, 300)

        if self.current_pattern == "circle_move":
            self.circle_center = (self.pos["x"], self.pos["y"])
            self.circle_angle = random.uniform(0, 2 * math.pi)
            self.circle_radius = random.randint(50, 150)
        elif self.current_pattern == "diagonal_move":
            dx = random.choice([-1, 1])
            dy = random.choice([-1, 1])
            self.diagonal_direction = (dx, dy)

    def pursue_pattern(self, px, py, p_speed):
        dx = px - self.pos["x"]
        dy = py - self.pos["y"]
        dist = math.hypot(dx, dy)
        if dist > 0:
            dx /= dist
            dy /= dist
            speed = p_speed * self.PURSUIT_SPEED_FACTOR
            self.pos["x"] += dx * speed
            self.pos["y"] += dy * speed

    def random_walk_pattern(self):
        if self.random_walk_timer <= 0:
            self.random_walk_angle = random.uniform(0, 2 * math.pi)
            self.random_walk_speed = self.base_speed * random.uniform(0.5, 2.0)
            self.random_walk_timer = random.randint(30, 90)
        else:
            self.random_walk_timer -= 1

        dx = math.cos(self.random_walk_angle) * self.random_walk_speed
        dy = math.sin(self.random_walk_angle) * self.random_walk_speed
        self.pos["x"] += dx
        self.pos["y"] += dy

    def circle_pattern(self):
        angle_increment = 0.02
        self.circle_angle += angle_increment
        dx = math.cos(self.circle_angle) * self.circle_radius
        dy = math.sin(self.circle_angle) * self.circle_radius
        self.pos["x"] = self.circle_center[0] + dx
        self.pos["y"] = self.circle_center[1] + dy

        if random.random() < 0.01:
            self.circle_radius += random.randint(-5, 5)
            self.circle_radius = max(20, min(200, self.circle_radius))

    def diagonal_pattern(self):
        if random.random() < 0.05:
            angle = math.atan2(self.diagonal_direction[1], self.diagonal_direction[0])
            angle += random.uniform(-0.3, 0.3)
            self.diagonal_direction = (math.cos(angle), math.sin(angle))

        speed = self.base_speed
        self.pos["x"] += self.diagonal_direction[0] * speed
        self.pos["y"] += self.diagonal_direction[1] * speed

    def initiate_forced_escape(self):
        dist_left = self.pos["x"]
        dist_right = (self.screen_width - self.size) - self.pos["x"]
        dist_top = self.pos["y"]
        dist_bottom = (self.screen_height - self.size) - self.pos["y"]

        min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
        if min_dist == dist_left:
            base_angle = 0.0
        elif min_dist == dist_right:
            base_angle = math.pi
        elif min_dist == dist_top:
            base_angle = math.pi / 2
        else:
            base_angle = 3 * math.pi / 2

        angle_variation = math.radians(30)
        self.forced_angle = base_angle + random.uniform(
            -angle_variation, angle_variation
        )
        self.forced_speed = self.base_speed * 1.0
        self.forced_escape_timer = random.randint(1, 30)
        self.state_timer = self.forced_escape_timer * 2

    def apply_forced_escape_movement(self):
        dx = math.cos(self.forced_angle) * self.forced_speed
        dy = math.sin(self.forced_angle) * self.forced_speed
        self.pos["x"] += dx
        self.pos["y"] += dy

    def hide(self):
        self.visible = False
        logging.info("EnemyTrain hidden for collision/respawn logic.")

    def show(self, current_time: int = 0):
        self.visible = True
        logging.info("EnemyTrain made visible again (no fade).")
