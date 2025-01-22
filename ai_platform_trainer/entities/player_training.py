# file: ai_platform_trainer/entities/player_training.py

import math
import random
import logging
import pygame
from ai_platform_trainer.entities.player import Player
from ai_platform_trainer.entities.missile import Missile
from ai_platform_trainer.utils.helpers import wrap_position


class PlayerTraining(Player):
    """
    Player class for 'training' mode.
    Inherits from base Player, overriding 'update' for AI patterns,
    and 'shoot_missile' for random angles, etc.
    """

    PATTERNS = ["random_walk", "circle_move", "diagonal_move"]

    def __init__(self, screen_width: int, screen_height: int):
        super().__init__(screen_width, screen_height, color=(0, 0, 139))
        # Overwrite base position with a random location
        self.position = {
            "x": random.randint(0, self.screen_width - self.size),
            "y": random.randint(0, self.screen_height - self.size),
        }
        self.desired_distance = 200
        self.margin = 20

        self.current_pattern = None
        self.state_timer = 0
        self.random_walk_timer = 0
        self.random_walk_angle = 0.0
        self.random_walk_speed = self.step
        self.circle_angle = 0.0
        self.circle_radius = 100
        self.diagonal_direction = (1, 1)

        # For smooth velocity-based movement
        self.velocity = {"x": 0.0, "y": 0.0}
        self.velocity_blend_factor = 0.2

        self.switch_pattern()
        logging.info("PlayerTraining initialized at %s", self.position)

    def reset(self) -> None:
        """
        Reset player to a random location and clear missiles.
        Then pick a new movement pattern.
        """
        self.position = {
            "x": random.randint(0, self.screen_width - self.size),
            "y": random.randint(0, self.screen_height - self.size),
        }
        self.missiles.clear()
        self.switch_pattern()
        logging.info("PlayerTraining has been reset to a random position.")

    def update(self, enemy_x: float, enemy_y: float) -> None:
        """
        Main update method for training:
         - Pick patterns based on distance to enemy
         - Possibly random or AI logic
         - Wrap around screen
        """
        dist = math.hypot(self.position["x"] - enemy_x, self.position["y"] - enemy_y)
        close_threshold = self.desired_distance - self.margin
        far_threshold = self.desired_distance + self.margin

        # Decrement pattern timer
        self.state_timer -= 1
        if self.state_timer <= 0:
            self.switch_pattern()

        if dist < close_threshold:
            self.random_walk_pattern(enemy_x, enemy_y)
        elif dist > far_threshold:
            if self.current_pattern == "circle_move":
                self.circle_pattern(enemy_x, enemy_y)
            elif self.current_pattern == "diagonal_move":
                self.diagonal_pattern(enemy_x, enemy_y)
            else:
                self.random_walk_pattern(enemy_x, enemy_y)
        else:
            if self.current_pattern == "random_walk":
                self.random_walk_pattern(enemy_x, enemy_y)
            elif self.current_pattern == "circle_move":
                self.circle_pattern(enemy_x, enemy_y)
            elif self.current_pattern == "diagonal_move":
                self.diagonal_pattern(enemy_x, enemy_y)

        # Wrap
        new_x, new_y = wrap_position(
            self.position["x"],
            self.position["y"],
            self.screen_width,
            self.screen_height,
            self.size,
        )
        self.position["x"], self.position["y"] = new_x, new_y

    def switch_pattern(self):
        new_pattern = self.current_pattern
        while new_pattern == self.current_pattern:
            new_pattern = random.choice(self.PATTERNS)
        self.current_pattern = new_pattern
        self.state_timer = random.randint(180, 300)
        if self.current_pattern == "circle_move":
            cx = max(self.size, min(self.screen_width - self.size, self.position["x"]))
            cy = max(self.size, min(self.screen_height - self.size, self.position["y"]))
            self.circle_center = (cx, cy)
            self.circle_angle = random.uniform(0, 2 * math.pi)
            self.circle_radius = random.randint(50, 150)
        elif self.current_pattern == "diagonal_move":
            dx = random.choice([-1, 1])
            dy = random.choice([-1, 1])
            self.diagonal_direction = (dx, dy)
        logging.debug(f"Switched pattern to {self.current_pattern} at {self.position}")

    def bias_angle_away_from_enemy(self, enemy_x, enemy_y, base_angle):
        dx = enemy_x - self.position["x"]
        dy = enemy_y - self.position["y"]
        dist = math.hypot(dx, dy)
        if dist == 0:
            return (base_angle + math.pi) % (2 * math.pi)

        enemy_angle = math.atan2(dy, dx)
        if dist < self.desired_distance - self.margin:
            bias_strength = math.radians(30)
        elif dist > self.desired_distance + self.margin:
            bias_strength = math.radians(15)
        else:
            bias_strength = math.radians(45)

        angle_diff = (base_angle - enemy_angle) % (2 * math.pi)
        if angle_diff < math.pi:
            new_angle = base_angle + bias_strength
        else:
            new_angle = base_angle - bias_strength

        return new_angle % (2 * math.pi)

    def move_with_velocity(self, ndx, ndy):
        target_vx = ndx * self.step
        target_vy = ndy * self.step
        self.velocity["x"] = (1 - self.velocity_blend_factor) * self.velocity[
            "x"
        ] + self.velocity_blend_factor * target_vx
        self.velocity["y"] = (1 - self.velocity_blend_factor) * self.velocity[
            "y"
        ] + self.velocity_blend_factor * target_vy
        self.position["x"] += self.velocity["x"]
        self.position["y"] += self.velocity["y"]

    def random_walk_pattern(self, enemy_x, enemy_y):
        if self.random_walk_timer <= 0:
            self.random_walk_angle = random.uniform(0, 2 * math.pi)
            self.random_walk_speed = self.step
            self.random_walk_timer = random.randint(30, 90)
        else:
            self.random_walk_timer -= 1

        angle = self.bias_angle_away_from_enemy(
            enemy_x, enemy_y, self.random_walk_angle
        )
        ndx = math.cos(angle)
        ndy = math.sin(angle)
        self.move_with_velocity(ndx, ndy)

    def circle_pattern(self, enemy_x, enemy_y):
        angle_increment = 0.02
        self.circle_angle += angle_increment

        desired_x = (
            self.circle_center[0] + math.cos(self.circle_angle) * self.circle_radius
        )
        desired_y = (
            self.circle_center[1] + math.sin(self.circle_angle) * self.circle_radius
        )

        dx = desired_x - self.position["x"]
        dy = desired_y - self.position["y"]

        base_angle = math.atan2(dy, dx)
        final_angle = self.bias_angle_away_from_enemy(enemy_x, enemy_y, base_angle)
        ndx = math.cos(final_angle)
        ndy = math.sin(final_angle)
        self.move_with_velocity(ndx, ndy)

        if random.random() < 0.01:
            self.circle_radius += random.randint(-2, 2)
            self.circle_radius = max(20, min(200, self.circle_radius))

    def diagonal_pattern(self, enemy_x, enemy_y):
        if random.random() < 0.02:
            angle = math.atan2(self.diagonal_direction[1], self.diagonal_direction[0])
            angle += random.uniform(-0.3, 0.3)
            self.diagonal_direction = (math.cos(angle), math.sin(angle))

        base_angle = math.atan2(self.diagonal_direction[1], self.diagonal_direction[0])
        final_angle = self.bias_angle_away_from_enemy(enemy_x, enemy_y, base_angle)
        self.diagonal_direction = (math.cos(final_angle), math.sin(final_angle))
        self.move_with_velocity(self.diagonal_direction[0], self.diagonal_direction[1])

    def shoot_missile(self, enemy_x: float, enemy_y: float) -> None:
        """
        Fires a missile toward the enemy with random offset + random lifespan,
        only one missile at a time, matching your original approach.
        """
        if len(self.missiles) == 0:
            missile_start_x = self.position["x"] + self.size // 2
            missile_start_y = self.position["y"] + self.size // 2

            dx = enemy_x - missile_start_x
            dy = enemy_y - missile_start_y
            angle = math.atan2(dy, dx)

            offset_degrees = random.uniform(-10, 10)
            angle += math.radians(offset_degrees)

            speed_val = 5.0
            vx = math.cos(angle) * speed_val
            vy = math.sin(angle) * speed_val

            lifespan = random.randint(500, 3000)
            birth_time = pygame.time.get_ticks()

            missile = Missile(
                x=missile_start_x,
                y=missile_start_y,
                speed=speed_val,
                vx=vx,
                vy=vy,
                lifespan=lifespan,
                birth_time=birth_time,
            )
            self.missiles.append(missile)
            logging.info(
                f"Training: Shot missile w offset={offset_degrees:.1f}°, angle={math.degrees(angle):.1f}°"
            )

    def update_missiles(self) -> None:
        """
        Let each missile move and remove it if it goes off-screen.
        Overriding if you have special training logic. Otherwise, you could
        just use the base method. We'll call super() for the default logic,
        but you can add extra code here if needed.
        """
        super().update_missiles()
