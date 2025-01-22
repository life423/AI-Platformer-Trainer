# file: ai_platform_trainer/gameplay/modes/play_mode.py
import logging
import pygame


class PlayModeManager:
    """
    Minimal bridging manager for 'play' mode:
     - Reads user input, translates it to an 'action' (dx, dy).
     - Calls env.step(action).
     - Renders or logs as needed.
    """

    def __init__(self, game):
        self.game = game  # reference to the main Game object

    def update(self) -> None:
        """
        Called each frame from Game when in 'play' mode.
        1) Build action from user input.
        2) Call env.step(action).
        3) If done, reset or handle game over logic.
        """
        # 1) Gather user input -> (dx, dy)
        dx, dy = self._get_player_input()

        # 2) Step environment
        observation, reward, done, info = self.game.env.step((dx, dy))

        logging.debug(f"[PlayMode] obs={observation}, reward={reward}, done={done}")

        if done:
            # Possibly show game-over menu or auto-reset
            logging.info("Play mode: environment signaled 'done'. Resetting.")
            self.game.env.reset(self.game.player, self.game.enemy)

    def _get_player_input(self):
        """
        Check key states to build an action (dx, dy).
        """
        keys = pygame.key.get_pressed()
        speed = self.game.player.step if self.game.player else 5
        dx = 0
        dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -speed
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -speed
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = speed

        return dx, dy
