"""
Button handling: debounced UP/DOWN with optional 1px spacing from edge.
Encapsulates state so main loop has no button globals.
"""
import time


class ButtonController:
    """Tracks two buttons (UP/DOWN) with debounce and calls into DisplayManager on press."""

    def __init__(self, button_up, button_down, debounce_seconds=0.3):
        self.button_up = button_up
        self.button_down = button_down
        self.debounce = debounce_seconds
        self._last_up_state = True
        self._last_up_time = 0.0
        self._last_down_state = True
        self._last_down_time = 0.0

    async def check(self, display_manager):
        """
        Check button states; on valid press, run toggle and update_games.
        Returns True if display_manager.update_games() was called (caller should reset timers).
        """
        current_time = time.monotonic()
        fetch_data = False

        # UP: toggle all vs live games
        current_up = self.button_up.value
        if (
            not current_up
            and self._last_up_state
            and (current_time - self._last_up_time) > self.debounce
        ):
            fetch_data, _ = display_manager.toggle_game_display()
            if fetch_data:
                self._last_up_time = current_time
                await display_manager.update_games()
                fetch_data = True
        self._last_up_state = current_up

        # DOWN: cycle sport
        current_down = self.button_down.value
        if (
            not current_down
            and self._last_down_state
            and (current_time - self._last_down_time) > self.debounce
        ):
            fetch_data, _ = display_manager.toggle_sport()
            if fetch_data:
                self._last_down_time = current_time
                await display_manager.update_games()
                fetch_data = True
        self._last_down_state = current_down

        return fetch_data
