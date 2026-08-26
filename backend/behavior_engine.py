from backend.action_engine import ActionEngine


class BehaviorEngine:
    """
    Decides how Cypher should physically react
    to semantic events.

    EventEngine:
        What happened?

    BehaviorEngine:
        How should Cypher react?

    ActionEngine:
        Perform the physical action.
    """

    def __init__(
        self,
        actions: ActionEngine,
    ):
        self.actions = actions

    def handle_event(
        self,
        event: dict,
    ) -> dict | None:

        event_name = event.get(
            "event"
        )

        if not event_name:
            return None

        # -----------------------------------------
        # LIGHT
        # -----------------------------------------

        if event_name == "LIGHTS_WENT_OFF":
            return self.actions.dark()

        if event_name == "LIGHTS_CAME_ON":
            return self.actions.idle()

        # -----------------------------------------
        # PRESENCE
        # -----------------------------------------

        if event_name == "OBJECT_ENTERED_RANGE":
            return self.actions.presence()

        if event_name == "OBJECT_LEFT_RANGE":
            return self.actions.idle()

        # Motion events currently don't need
        # a physical reaction.
        return None