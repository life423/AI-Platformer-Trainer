# file: ai_platform_trainer/gameplay/modes/training_mode.py
import logging
import random

import math

class TrainingMode:
    """
    Minimal bridging manager for 'train' mode:
     - Possibly picks AI or random actions for the player/enemy.
     - Calls env.step(action).
     - Logs episodes or transitions.
    """

    def __init__(self, game):
        self.game = game  # main Game object
        self.episode_reward = 0.0
        self.episode_count = 0

    def update(self):
        """
        Called each frame from Game when in 'train' mode.
        1) Decide an action (dx, dy) from an AI policy or random.
        2) env.step(action)
        3) Aggregate rewards, check if done -> reset
        """
        # 1) Example: random action
        dx, dy = self._random_action()

        # 2) Step environment
        obs, reward, done, info = self.game.env.step((dx, dy))
        self.episode_reward += reward

        logging.debug(f"[TrainingMode] obs={obs}, reward={reward}, done={done}")

        # 3) If done, log episode and reset
        if done:
            self.episode_count += 1
            logging.info(
                f"Episode {self.episode_count} finished. Total reward={self.episode_reward:.2f}"
            )
            self.episode_reward = 0.0
            self.game.env.reset(
                self.game.player, self.game.enemy, data_logger=self.game.data_logger
            )

    def _random_action(self):
        """
        Generate a random (dx, dy). In real RL, you'd call a policy network.
        """
        speed = self.game.player.step if self.game.player else 5
        # random direction
        angle = random.uniform(0, 2.0 * 3.14159)
        dx = speed * math.cos(angle)
        dy = speed * math.sin(angle)
        return dx, dy
