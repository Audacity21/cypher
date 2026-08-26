from copy import deepcopy

from backend.world_state import WorldState


class WorldStateManager:
    def __init__(self):
        self.current = WorldState()
        self.previous = WorldState()

    def update(self, sensor_data: dict) -> WorldState:
        self.previous = deepcopy(self.current)

        self.current.update(
            sensor_data
        )

        return self.current

    def get_current(self) -> WorldState:
        return self.current

    def get_previous(self) -> WorldState:
        return self.previous

    def get_current_dict(self) -> dict:
        return self.current.to_dict()

    def get_previous_dict(self) -> dict:
        return self.previous.to_dict()